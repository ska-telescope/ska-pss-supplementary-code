# Proposal: Start cheetah_pipeline at deployment time and use gRPC for all scan configurations

## Currently planned behaviour

PSS is to be deployed in a state where cheetah_pipeline is not yet running. During AssignResources(), PSS.LMC will reserve the nodes on which cheetah will run for a subarray. Before the first scan, Configure() writes the XML configuration for that first scan to disk on the target node and will start cheetah_pipeline remotely using ssh/paramiko. Scan() will then cause cheetah to process data. Endscan() stops scan processing but will leave cheetah running. Subsequent calls to Configure() then behave differently: instead of starting cheetah, they will update the already-running cheetah via gRPC. 

The means Configure(), will have two distinct behaviours: 

* For the first scan in an execution block, it must create the initial configuration file and start the cheetah process
* For later scans, it must send an updated configuration to an already-running cheetah process. 

This introduces avoidable statefulness into PSS.LMC. In particular, PSS.LMC must know whether a given Configure() call corresponds to the first scan or a later scan, and must choose a different implementation path accordingly. That makes the behaviour of Configure dependent on scan position rather than on the command alone. 

## Suggested behaviour

Instead, cheetah_pipeline could be started at deployment time, using a minimal default configuration, whose only purpose is to allow the process to initialise and expose its control interface. Once cheetah is running, every call to Configure() would send a complete scan configuration via gRPC. 

This removes the need for Configure() to distinguish between "first scan" and "subsequent scan". The first scan is configured in the same way as all other scans. 

## Benefits

The  main benefit will be reduced control flow complexity in PSS.LMC. Configure() no longer needs to track whether cheetah has already been started, or whether we're in scan 1 in the Execution Block, or whether is should use a file/SSH path rather than a gRPC path. It would always perform the same operation; issue the complete scan configuration over gRPC. 

Additionally, cheetah process lifetime becomes a deployment/runtime management concern, whereas scan configuration remains a control concern. 

A further advantage is that PSS.LMC no longer needs to implement SSH/Paramiko in the scan-control path. 

# Handling changes to cheetah CLI arguments

Some cheetah options are naturally process-level options rather than scan/configuration level options. Examples include the selected pipeline type (SinglePulse, FDAS, Empty, etc), the data source (stream or file, configuration file path, and logging level. 

These are currently handled by helm values but changing them post-deployment would require restarting cheetah/redeployment. The helm chart can template the cheetah command line arguments from values such as 

```yaml
cheetah:
  config: /etc/cheetah/configs/default-sps-sigproc_out.xml
  pipeline: SinglePulse
  source: udp_low_lite
  loglevel: control
```
A helm upgrade can change these values and cause kubernetes to roll out a new pod with updated command line arguments. The provides a controlled way to change process-level settings without requiring PSS.LMC to manage process creation directly. 

Similarly, if PSS is not required and the node can be used for other purposes, the helm release remain deployed whilst the deployment is scaled to zero replicas, analogous to stopping a service with systemd without uninstalling it. 




