add_library(kafka_producer STATIC
    src/KafkaProducerConfig.cpp
    src/SpccCandidateMessage.cpp
    src/KafkaProducer.cpp
)
target_include_directories(kafka_producer
    PUBLIC  ${CMAKE_CURRENT_SOURCE_DIR}/include ${MSGPACK_INCLUDE_DIR}
)
target_link_libraries(kafka_producer
    PUBLIC  PkgConfig::RDKAFKA OpenSSL::Crypto ${UUID_LIB}
)

add_executable(kafka_producer_cli src/main.cpp)
target_link_libraries(kafka_producer_cli PRIVATE kafka_producer)
