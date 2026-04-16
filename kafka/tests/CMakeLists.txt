add_executable(test_kafka_producer test_kafka_producer.cpp)
target_link_libraries(test_kafka_producer
    PRIVATE kafka_producer gtest_main PkgConfig::RDKAFKA
)
include(GoogleTest)
gtest_discover_tests(test_kafka_producer
    PROPERTIES LABELS "integration"
)
