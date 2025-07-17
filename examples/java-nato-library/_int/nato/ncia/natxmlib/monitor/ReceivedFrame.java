/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib.monitor;

import _int.nato.ncia.natxmlib.JTIDSDataFrame;
import java.time.Instant;

/**
 *
 * @author mike
 */
public class ReceivedFrame {
    protected final boolean bim; // aka TIM/BIM
    protected final JTIDSDataFrame frame;
    protected final Instant receiveTime;
    protected final long sequenceNumber;
    
    public ReceivedFrame(boolean isBIM, JTIDSDataFrame frame, Instant receiveTime, long sequenceNumber) {
        this.bim = isBIM;
        this.frame = frame;
        this.receiveTime = receiveTime;
        this.sequenceNumber=sequenceNumber;
    }

    public boolean isBIM() {
        return bim;
    }

    public JTIDSDataFrame getFrame() {
        return frame;
    }

    public Instant getReceiveTime() {
        return receiveTime;
    }

    public long getSequenceNumber() {
        return sequenceNumber;
    }
    
}
