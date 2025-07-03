#pragma once

#include <string>
#include <vector>
#include <sqlite3.h>
#include <zlib.h>

class DataProcessor {
public:
    DataProcessor();
    ~DataProcessor();
    
    void process_data(const std::string& data);
    std::vector<uint8_t> compress_data(const std::string& data);
    
private:
    sqlite3* db_;
};