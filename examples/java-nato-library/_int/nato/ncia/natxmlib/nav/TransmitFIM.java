/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib.nav;

import fxmlib.fxm.FIM;
import java.time.Instant;

/**
 *
 * @author mike
 */
public class TransmitFIM implements NAVMessage {
    protected final Instant systemTime;    
    protected final FIM fim;

    public TransmitFIM(Instant systemTime, FIM fim) {
        this.systemTime = systemTime;
        this.fim = fim;
    }

    public Instant getSystemTime() {
        return systemTime;
    }

    public FIM getFim() {
        return fim;
    }

    
    
}
