/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib.clock;

import java.time.Instant;
import java.time.ZoneId;

/**
 *
 * @author mike
 */
public class SystemClock implements SimpleClock {
    protected static final SystemClock INSTANCE = new SystemClock();
    public final static ZoneId UTC = ZoneId.of("UTC");
    
    public static SystemClock getInstance() {
        return INSTANCE;
    }

    private SystemClock() {
        isReplay=false;
    }
    
    protected boolean isReplay;
    protected Instant replayTime=null;
    @Override
    public Instant now() {
        if(isReplay) {
            return replayTime;
        }else{
            return Instant.now();
        }
    }
    public void setReplayMode() {
        isReplay=true;
    }

    public void setReplayTime(Instant replayTime) {
        this.replayTime = replayTime;
    }

    @Override
    public boolean isRunning() {
        if(!isReplay) {
            return true;
        }else{
            return replayTime!=null;
        }
    }    
}
