# Proposal: Start cheetah_pipeline at deployment time and use gRPC for all scan configurations

## Currently planned behaviour

PSS is to be deployed in a state where `cheetah_pipeline` is not yet running. During `AssignResources()`, PSS.LMC will reserve the nodes on which cheetah will run for a subarray. Before the first scan, `Configure()` writes the XML configuration for that first scan to disk on the target node and will start `cheetah_pipeline` remotely using ssh/paramiko. `Scan()` will then cause cheetah to process data. `Endscan()` stops scan processing but will leave cheetah running. Subsequent calls to `Configure()` then behave differently: instead of starting cheetah, they will update the already-running cheetah via gRPC. 

The means `Configure()`, will have two distinct behaviours: 

* For the first scan in an execution block, it must create the initial configuration file and start the cheetah process
* For later scans, it must send an updated configuration to an already-running cheetah process. 

This introduces avoidable statefulness into PSS.LMC. In particular, PSS.LMC must know whether a given `Configure()` call corresponds to the first scan or a later scan, and must choose a different implementation path accordingly. That makes the behaviour of `Configure()` dependent on scan position rather than on the command alone. 

## Suggested behaviour

Instead, `cheetah_pipeline` could be started at deployment time, using a minimal default configuration, whose only purpose is to allow the process to initialise and expose its control interface. Once cheetah is running, every call to `Configure()` would send a complete scan configuration via gRPC. 

This removes the need for `Configure()` to distinguish between "first scan" and "subsequent scan". The first scan is configured in the same way as all other scans. 

## Benefits

The  main benefit will be reduced control flow complexity in PSS.LMC. `Configure()` no longer needs to track whether cheetah has already been started, or whether we're in scan 1 in the Execution Block, or whether is should use a file/SSH path rather than a gRPC path. It would always perform the same operation; issue the complete scan configuration over gRPC. 

Additionally, cheetah process lifetime becomes a deployment/runtime management concern, whereas scan configuration remains a control concern. 

A further advantage is that PSS.LMC no longer needs to implement SSH/Paramiko in the scan-control path. 

## Handling changes to cheetah CLI arguments

Some cheetah options are naturally process-level options rather than scan/configuration level options. Examples include the selected pipeline type (SinglePulse, FDAS, Empty, etc), the data source (stream or file, configuration file path, and logging level. 

These are currently handled by helm values but changing them post-deployment would require restarting cheetah/redeployment. The helm chart can template the cheetah command line arguments from values such as 

```yaml
cheetah:
  config: /etc/cheetah/configs/default-sps-sigproc_out.xml
  pipeline: SinglePulse
  source: udp_low_lite
  loglevel: control
```
A `helm upgrade` can change these values and cause kubernetes to roll out a new pod with updated command line arguments. The provides a controlled way to change process-level settings without requiring PSS.LMC to manage process creation directly. 

Similarly, if PSS is not required and the node can be used for other purposes, the helm release remain deployed whilst the deployment is scaled to zero replicas, analogous to stopping a service with systemd without uninstalling it. 

The cheetah CLI options could be supplied to the deployment via a `ConfigMap`. This keeps deployment-time configuration, such as the initial XML path, data source, etc, separate from the container image. 

One subtlety is that changing a `ConfigMap` does not automatically restart pods that consume it through environment variables. These are read when the container starts so an already running cheetah pod will continue using the old values until the pod is restarted. To handle this cleanly, the deployment template could include a checksum annotation based on the rendered `ConfigMap`. 

When the helm values change (using a `helm upgrade`) the checksum will change too. Because this annotation is part of the pod template, Kubernetes sees the deployment as changed and performs a normal rolling update. This gives a reliable way to trigger a cheetah restart when process-level options change, without manually deleting pods or redeploying the whole chart. 

# Example

In this example, I deployed the SKA CICD environment on `dokimi` (PSS development server - runs Ubuntu 22 LTS)

```bash
cd ska-cicd-deploy-minikube
make all DRIVER=docker MEM=16384 CPUS=16
kubectl get pods -A

NAMESPACE            NAME                                            READY   STATUS    RESTARTS   AGE
cert-manager         cert-manager-848cd5ff9f-pmbrb                   1/1     Running   0          4m37s
cert-manager         cert-manager-cainjector-9f76b67db-nbvh5         1/1     Running   0          4m37s
cert-manager         cert-manager-webhook-7699796787-7z8jc           1/1     Running   0          4m37s
extdns               extdns-coredns-66658d8d8c-tjnpx                 1/1     Running   0          59s
haproxy-controller   haproxy-kubernetes-ingress-79845df6bb-pbrml     1/1     Running   0          83s
haproxy-controller   haproxy-kubernetes-ingress-79845df6bb-s986p     1/1     Running   0          83s
ingress-nginx        ingress-nginx-controller-56f47c86d-9svzv        1/1     Running   0          2m
kube-system          cilium-8b7vj                                    1/1     Running   0          4m40s
kube-system          cilium-envoy-dfbmd                              1/1     Running   0          4m40s
kube-system          cilium-operator-d4558f9cf-g9c46                 1/1     Running   0          3m22s
kube-system          coredns-68648c7bf8-lfcx4                        1/1     Running   0          64s
kube-system          csi-hostpath-attacher-0                         1/1     Running   0          3m16s
kube-system          csi-hostpath-resizer-0                          1/1     Running   0          3m16s
kube-system          csi-hostpathplugin-2dbg5                        6/6     Running   0          3m16s
kube-system          etcd-minikube                                   1/1     Running   0          4m51s
kube-system          hubble-relay-56f7c65878-fsmkv                   1/1     Running   0          4m40s
kube-system          hubble-ui-67d8bff4c4-2g526                      2/2     Running   0          4m40s
kube-system          kube-apiserver-minikube                         1/1     Running   0          4m51s
kube-system          kube-controller-manager-minikube                1/1     Running   0          4m51s
kube-system          kube-scheduler-minikube                         1/1     Running   0          4m51s
kube-system          metrics-server-9d74bb658-9b7gd                  1/1     Running   0          3m18s
kube-system          snapshot-controller-6588d87457-hrn26            1/1     Running   0          2m52s
kube-system          snapshot-controller-6588d87457-mzhqv            1/1     Running   0          2m52s
kube-system          storage-provisioner                             1/1     Running   0          4m50s
metallb-system       controller-66bdd896c6-tcwxg                     1/1     Running   0          2m46s
metallb-system       speaker-xn2dr                                   1/1     Running   0          2m46s
nginx-ingress-oss    nginx-ingress-oss-controller-756f576df8-dmzfn   1/1     Running   0          85s
```

## Step 1 - build container image

This is represented in the example Dockerfile. As this is just an exmple, I don't apt install the deb archive for cheetah, instead I copied in a `cheetah_pipeline` binary from a previous build. I also copy in some example default config files to /etc/cheetah/configs. No ssh is installed or started in this example and the `ENTRYPOINT` is set to be the `cheetah_pipeline` executable path. 

```bash
cd ska-pss-supplmentary-code/cheetah_helm_charts
docker build --network=host -t cheetah-demo:0.1 .
minikube image load cheetah-demo:0.1 
docker image ls | grep demo

cheetah-demo                                                            0.1                     df7fef990bb1   About a minute ago   183MB
```
