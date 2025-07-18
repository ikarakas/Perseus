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
public class TimeFilter2 extends TimeFilter {

    public TimeFilter2(SimpleClock systemClock) {        
        super(systemClock);
    }

    protected Measurement lastM = null;

    @Override
    protected void update(Measurement m) {
        update(m, false);
    }

    protected void update(Measurement m, boolean test) {
        if (lastM == null) {
            lastM = m;
            offset = Duration.between(m.systemTime, m.getTime());
            return;
        }
        Duration elapsedUTC = Duration.between(lastM.getTime(), m.getTime());
        Instant eST = lastM.systemTime.plus(elapsedUTC);
        Duration err = Duration.between(m.systemTime, eST);
        double err_s = err.toNanos() / 1_000_000_000.0;
        if (Math.abs(err_s) < 0.001) {

        } else {
            if (Math.abs(err_s) >= 0.1) {
                if (++missCount >= 3) {
                    lastM = null;
                    reset();
                    return;
                } else {
                    return;
                }
            }
        }
        missCount = 0;
        offset = Duration.between(m.systemTime, m.getTime());
        lastM = m;
        
        if(Math.abs(err_s)<0.02) {
           // System.out.println("####GPSTIME##;"+err_s+";"+m.mTOD+";"+getTime(m.systemTime));
        }

    }
}


