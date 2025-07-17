/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib.clock;

import java.time.Duration;
import java.time.Instant;

/**
 *
 * @author mike
 */
public class OffsetClock implements SimpleClock {
    protected final SimpleClock baseClock;
    protected Duration offset;

    public OffsetClock(SimpleClock baseClock, Duration offset) {
        this.baseClock = baseClock;
        this.offset = offset;
    }
    public OffsetClock(SimpleClock baseClock) {
        this(baseClock,null);
    }

    @Override
    public Instant now() {
        if(!isRunning()) {
            throw new RuntimeException("clock is not running");
        }
        return baseClock.now().plus(offset);
    }
    public Instant getBaseTime(Instant clockTime) {
        if(offset==null) {
            throw new RuntimeException("clock offset it not valid");
        }
        return clockTime.minus(offset);    
    } 
    public Duration getOffset() {
        return offset;
    }

    public void setOffset(Duration offset) {
        this.offset = offset;
    }
    public void update(Instant baseTime, Instant offsetClockTime) {
         Duration _offset = Duration.between(baseTime, offsetClockTime);
         setOffset(offset);
    }
    public void update(Instant offsetClockTime) {
         Duration _offset = Duration.between(baseClock.now(), offsetClockTime);
         setOffset(offset);
    }
    @Override
    public boolean isRunning() {
        return baseClock.isRunning() && (offset!=null);
    }
    
}
