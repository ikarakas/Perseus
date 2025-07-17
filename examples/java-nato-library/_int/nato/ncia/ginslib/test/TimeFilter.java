/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.ginslib.test;

import _int.nato.ncia.natxmlib.clock.SimpleClock;
import java.time.Duration;
import java.time.Instant;

/**
 *
 * @author mike
 */
public class TimeFilter implements SimpleClock {
    
    protected Duration offset = null;
    protected Duration lastTOD = null;
    protected Instant day = null;
    protected Instant systemTimeOfDay = null;
    protected int missCount = 0;
    protected final SimpleClock systemClock;
    protected final Duration sigmaDriftPerScond = Duration.ofNanos(10_000);
    protected double sigmaP=0.0;
    
    public TimeFilter(SimpleClock systemClock) {
        this.systemClock=systemClock;
    }

    public static Duration calculateTOD(Instant time) {
        long secondOfDay=time.getEpochSecond()%86_400;
        return Duration.ofSeconds(secondOfDay).plus(Duration.ofNanos(time.getNano()%1_000_000_000));        
    }
    public static Instant calculateDAY(Instant time) {
        return time.minus(calculateTOD(time));
    }
    
    public void updateDAY(Instant systemTime, Instant day) {
        if (this.day == null) {
            this.day = day;
            systemTimeOfDay = systemTime;
        } else {
            this.day = day; //$TODO
            systemTimeOfDay = systemTime;            
        }
    }
    public void updateTOD(Instant systemTime, Duration tod, Duration sigmaTOD) {
        if(day==null) {
            return;
        }
        if (lastTOD == null) {
            lastTOD = tod;
        } else {
            Duration dt = tod.minus(lastTOD);
            if (dt.toMillis() < 800) {
                return;
            }
            Measurement m = new Measurement(systemTime, tod, sigmaTOD, day, Duration.ofMillis(30));
            update(m);
            lastTOD = tod;
        }
    }
    public Instant getTime(Instant systemTime) {
        if(offset==null) {
            return null;
        }else{
            return systemTime.plus(offset);
        }
    }
    
    protected void reset() {
        offset = null;
        lastTOD = null;
        missCount = 0;
    }
    
    protected void update(Measurement m) {
        Duration moffset = Duration.between(m.systemTime, m.getTime());
        
        if(offset==null) {
            offset=moffset;
            return;
        }
        Duration oerr = offset.minus(moffset);
        double oerr_sec = oerr.toNanos() / 1_000_000_000.0;
        if (Math.abs(oerr_sec) < 0.001) {
            offset = offset.minus(oerr);
        } else {
            if (Math.abs(oerr_sec) > 0.1) {
                if (++missCount >= 3) {
                    offset = moffset;
                } else {
                    return;
                }
            }
        }
        missCount = 0;
//        System.out.println("###"+m.mTOD+";"+getTime(m.systemTime));
        
    }

    @Override
    public Instant now() {
        return getTime(systemClock.now());
    }

    @Override
    public boolean isRunning() {
        return offset!=null;
    }
    public class Measurement {
        protected final Instant     systemTime;
        protected final Duration    mTOD;
        protected final Instant     mDAY;
        protected final Duration    sigmaTOD;
        protected final Duration    mDelay;
        
        protected Instant getTime() {
            return mDAY.plus(mTOD);
        }
        public Measurement(Instant systemTime, Duration mTOD, Duration sigmaTOD, Instant mDAY, Duration mDelay) {
            this.systemTime = systemTime;
            this.mTOD = mTOD;
            this.mDAY = mDAY;
            this.sigmaTOD = sigmaTOD;
            this.mDelay = mDelay;
        }
    }
   
    
}
