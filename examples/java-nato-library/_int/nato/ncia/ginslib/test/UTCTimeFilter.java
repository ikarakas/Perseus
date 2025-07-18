/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.ginslib.test;

import java.time.Duration;
import java.time.Instant;
import java.util.LinkedList;

/**
 *
 * @author mike
 */
public class UTCTimeFilter {
    protected Instant lastUTC;
    protected Instant lastSystemTime;
       
    protected Double lastErr=null;
    protected final LinkedList<Duration> offsetList = new LinkedList<>();
    protected Duration offset=Duration.ZERO;
    protected boolean isValid=false;
    protected final static int MAX_SAMPLES = 64;
    protected static long nextFilterId=1;
    protected final long filterId;
    protected boolean resetted=false;
    
    public UTCTimeFilter() {
        this.filterId=nextFilterId++;
    }
    
    protected Duration getMinOffset() {
        synchronized (offsetList) {
            if(offsetList.isEmpty()) {
                return Duration.ZERO;
            }
            Duration min=offsetList.getFirst();
            for(Duration entry : offsetList) {
                if(entry.compareTo(min)<0) {
                    min=entry;
                }
            }
            return min;            
        }
    }
    protected long missCount=0;
    
    public void update(Instant utc, Instant systemTime) {
        lastUTC = utc;
        lastSystemTime = systemTime;
        Duration lastOffset = Duration.between(utc, systemTime);
        synchronized (offsetList) {
            if(offsetList.isEmpty()) {
                offsetList.add(lastOffset);
                offset=lastOffset;
                isValid=true;
                return;
            }
        }        
        Duration min = getMinOffset();
        Duration above = lastOffset.minus(min);
        lastErr = above.toSeconds()+above.getNano()/1_000_000_000.0;
        
        double lastOffset_sec=(lastOffset.getSeconds()%3600)+(lastOffset.toNanosPart()/1_000_000_000.0);
        if (above.abs().compareTo(Duration.ofMillis(300)) >= 0) {
            missCount++;
//            System.out.println("#TIME_FILTER_MISS;"+filterId+";"+utc+";"+above);
            if (missCount >= 3) {
                synchronized (offsetList) {
                    offsetList.clear();
                    offsetList.add(lastOffset);
                    missCount=0;
                    resetted=true;
                }
                System.out.println("#TIME_FILTER_RESET;"+filterId+";"+utc+";"+above);
            }
            return;
        }else{
            missCount=0;
            resetted=false;
        }
        synchronized (offsetList) {
            if(offsetList.size()>=MAX_SAMPLES) {
                offsetList.removeFirst();
            }
            offsetList.add(lastOffset);
            this.offset=getMinOffset();
        }
        double offset_sec=(offset.getSeconds()%3600)+(offset.toNanosPart()/1_000_000_000.0);
//        System.out.println("#TIME_FILTER_UPDATE;"+filterId+";"+lastUTC+";"+offset_sec+";"+lastOffset_sec+";"+lastErr);
        
    }
    public Instant calculateST(Instant utc) {
        if (isValid) {
            return utc.plus(offset);
        } else {
            return null;
        }
    }

    public Instant calculateUTC(Instant systemTime) {
        if (isValid(systemTime)) {
            return systemTime.minus(offset);
        } else {
            return null;
        }
    }

    public boolean isResetted() {
        return resetted;
    }
    
    public void reset() {
        synchronized (offsetList) {
            offsetList.clear();
            isValid = false;
            resetted=true;
        }
    }

    public double getSigma() {
        return 0.0;
    }

    public Duration getOffset() {
        return offset;
    }

    public int getCount() {
        synchronized (offsetList) {
            return offsetList.size();
        }
    }

    public Double getLastError() {
        return lastErr;
    }
    public boolean isValid(Instant systemTime) {
        if(lastSystemTime==null) {
            return false;
        }
        Duration age = Duration.between(lastSystemTime, systemTime);
        if(age.compareTo(Duration.ofMinutes(30))<0) {
            return isValid;
        }else{
            return false;
        }
    }
    public static final UTCTimeFilter INVALID=new UTCTimeFilter(){
        @Override
        public boolean isValid(Instant systemTime) {
            return false;
        }     

        @Override
        public Instant calculateUTC(Instant systemTime) {
            return null;
        }

        @Override
        public Instant calculateST(Instant utc) {
            return null;
        }

        @Override
        public Duration getOffset() {
            return null;
        }

        @Override
        public void update(Instant utc, Instant systemTime) {           
        }
        
    };
}
