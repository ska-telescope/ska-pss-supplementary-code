add_executable(test_kafka_producer test_kafka_producer.cpp)
target_link_libraries(test_kafka_producer
    PRIVATE kafka_producer gtest_main PkgConfig::RDKAFKA
)
include(GoogleTest)
gtest_discover_tests(test_kafka_producer
    PROPERTIES LABELS "all"
    TEST_FILTER "*"
)

# Re-register the offline tests under the unit label so
# `ctest -L unit` runs broker-free.
add_test(NAME unit_offline
         COMMAND test_kafka_producer
                 --gtest_filter=KafkaProducerConfigTest.*:SpccCandidateMessageTest.*:SpccInputLoaderTest.*)
set_tests_properties(unit_offline PROPERTIES LABELS "unit")
