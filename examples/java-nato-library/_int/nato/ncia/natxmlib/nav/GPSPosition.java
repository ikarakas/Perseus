/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib.nav;

import _int.nato.ncia.ginslib.GINS_T09;
import java.time.Instant;

/**
 *
 * @author mike
 */
public class GPSPosition implements NAVMessage {
    protected Instant systemTime;
    protected Instant utcTime;
    protected GINS_T09 t09;

    public GPSPosition(Instant systemTime, Instant utcTime, GINS_T09 t09) {
        this.systemTime = systemTime;
        this.utcTime = utcTime;
        this.t09 = t09;
    }

    @Override
    public Instant getSystemTime() {
        return systemTime;
    }
    
    
}
