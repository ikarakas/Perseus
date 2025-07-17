/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib.nav;

import java.time.Instant;

/**
 *
 * @author mike
 */
public class GPSTimePulse implements NAVMessage {
    protected Instant systemTime;
    protected Instant utcTime;
    protected int timeFOM;
    
    public GPSTimePulse(Instant systemTime, Instant utcTime, int timeFOM) {
        this.systemTime = systemTime;
        this.utcTime = utcTime;
        this.timeFOM=timeFOM;
    }
    
    
    public int getTimeFOM() {
        return timeFOM;
    }

    @Override
    public Instant getSystemTime() {
        return systemTime;
    }
    
}
