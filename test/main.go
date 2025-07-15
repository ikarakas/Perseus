package main

import (
	"fmt"
	"log"
	"os"
	"time"
)

const (
	logFile     = "/var/log/app.log"
	maxFileSize = 1024 * 1024 // 1MB
	interval    = 30 * time.Second
)

func main() {
	log.Println("Starting Go application service...")
	
	for {
		// Check file size and rotate if needed
		if err := rotateLogIfNeeded(); err != nil {
			log.Printf("Error rotating log: %v", err)
		}
		
		// Write log message
		if err := writeLogMessage(); err != nil {
			log.Printf("Error writing log message: %v", err)
		}
		
		// Wait for next interval
		time.Sleep(interval)
	}
}

func rotateLogIfNeeded() error {
	info, err := os.Stat(logFile)
	if err != nil {
		// File doesn't exist, which is fine
		if os.IsNotExist(err) {
			return nil
		}
		return err
	}
	
	if info.Size() >= maxFileSize {
		log.Printf("Log file size (%d bytes) exceeds limit, rotating...", info.Size())
		if err := os.Remove(logFile); err != nil {
			return err
		}
		log.Println("Log file rotated")
	}
	
	return nil
}

func writeLogMessage() error {
	f, err := os.OpenFile(logFile, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		return err
	}
	defer f.Close()
	
	timestamp := time.Now().Format("2006-01-02 15:04:05")
	message := fmt.Sprintf("[%s] Hello from GO !!!\n", timestamp)
	
	if _, err := f.WriteString(message); err != nil {
		return err
	}
	
	log.Printf("Logged: %s", message[:len(message)-1]) // Remove newline for log output
	return nil
}
