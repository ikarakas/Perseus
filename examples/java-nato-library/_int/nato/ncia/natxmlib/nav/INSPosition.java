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
public class INSPosition implements NAVMessage {
    protected Instant systemTime;
    protected Instant utcTime;

    public INSPosition(Instant systemTime, Instant utcTime) {
        this.systemTime = systemTime;
        this.utcTime = utcTime;
    }

    @Override
    public Instant getSystemTime() {
        return systemTime;
    }
    
   
    
}
