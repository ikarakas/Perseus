package _int.nato.ncia.ginslib;

import java.time.Duration;
import java.time.Instant;
import java.time.ZonedDateTime;

/**
 *
 * @author mike
 */
public class GINS_T20 extends GINSMessage {    
    protected int hour;
    protected int minute;
    protected int second;
    protected int dayOfYear;
    protected int tfom;
    //tfom
    //15=no information
    //9=>10ms or fault
    //8=1ms to 10ms
    //7=100mus to 1ms
    //6=10mus to 100mus
    //5=1mus to 10mus
    //4=100ns to 1mus
    //3=10ns to 100ns
    //2=1ns to 10ns
    //1=better than 1ns    
    //0=proper operation
    public GINS_T20(int hour, int minute, int second, int dayOfYear, int tfom) {
        this.hour = hour;
        this.minute = minute;
        this.second = second;
        this.dayOfYear = dayOfYear;
        this.tfom = tfom;
    }
    
    public GINS_T20(short[] wd) {
        super("T-20");
        hour = ((wd[0]>>12)&0xf)*10+((wd[0]>>8)&0xf);
        minute = ((wd[0]>>4)&0xf)*10+((wd[0])&0xf);
        second = ((wd[1]>>12)&0xf)*10+((wd[1]>>8)&0xf);
        dayOfYear = ((wd[1]>>4)&0xf)*100+((wd[1])&0xf)*10+((wd[2]>>12)&0xf);
        tfom = ((wd[3]>>12)&0xf);
    }
    public static GINS_T20 decode(short[] wd) {
        return new GINS_T20(wd);
    }
    @Override
    public String toString() {
        return String.format("%03d-%02d:%02d:%02d [%02d]", dayOfYear,hour,minute,second,tfom);
    }

    public int getHour() {
        return hour;
    }

    public int getMinute() {
        return minute;
    }

    public int getSecond() {
        return second;
    }

    public int getDayOfYear() {
        return dayOfYear;
    }

    public int getTFOM() {
        return tfom;
    }
    public Duration getTimeOfDay() {
        return Duration.ofSeconds(getSecond()+getMinute()*60+getHour()*3600);        
    }
    public Duration getTimeOfYear() {
        return Duration.ofSeconds(getSecond()+getMinute()*60L+getHour()*3600L+getDayOfYear()*24L*3600L);        
    }
    public Instant toInstant(int year) {
        ZonedDateTime utc = ZonedDateTime.now(UTC)
                .withYear(year)
                .withDayOfYear(getDayOfYear())
                .withHour(getHour())
                .withMinute(getMinute())
                .withSecond(getSecond())
                .withNano(0);
        return utc.toInstant();
    }
}
