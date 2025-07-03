package com.example;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.commons.lang3.StringUtils;

@SpringBootApplication
@RestController
public class Application {
    
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
    
    @GetMapping("/")
    public String hello() {
        // Using Apache Commons Lang
        String message = StringUtils.capitalize("hello world from sbom test app");
        
        // Using Jackson for JSON processing
        ObjectMapper mapper = new ObjectMapper();
        
        return message;
    }
}