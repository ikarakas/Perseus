/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib.fields;

import java.time.Duration;
import java.time.Instant;

/**
 *
 * @author mike
 */
public class TimeStamp {
    protected int hrs;
    protected int min;
    protected int sec;
    protected int micros;

    public TimeStamp(int hrs, int min, int sec, int micros) {
        this.hrs = hrs;
        this.min = min;
        this.sec = sec;
        this.micros = micros;
    }
  
    public Duration toDuration() {
        return Duration.ofHours(hrs).plus(Duration.ofMinutes(min)).plus(Duration.ofSeconds(sec)).plus(Duration.ofNanos(micros*1000));        
    }
    
    @Override
    public String toString() {
        return String.format("%02d:%02d:%02d.%06d", hrs,min,sec,micros);
    }

    public int getHrs() {
        return hrs;
    }

    public int getMin() {
        return min;
    }

    public int getSec() {
        return sec;
    }

    public int getMicros() {
        return micros;
    }
    public static TimeStamp fromInstant(Instant instant) {
        int millis_of_day = (int)(instant.toEpochMilli() % 86_400_000);
        int tsecs=millis_of_day/1000;
        int ms=millis_of_day%1000;
        int hrs=tsecs/3600;
        tsecs-=hrs*3600;
        int min=tsecs/60;
        int sec=tsecs%60;
        return new TimeStamp(hrs, min, sec, ms*1000);        
    }
    public static TimeStamp fromDuration(Duration d) {
        if(d==null) {
            return null;
        }
        int tsec=(int)(d.getSeconds());
        int micros=d.getNano()/1000;
        int hrs=tsec/3600;
        int min=(tsec-hrs*3600)/60;
        int sec=tsec%60;
        return new TimeStamp(hrs, min, sec, micros);
    }
}
