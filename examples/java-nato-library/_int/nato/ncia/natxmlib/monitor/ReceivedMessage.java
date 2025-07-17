/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib.monitor;

import _int.nato.ncia.natxmlib.messages.NATxM;
import java.time.Instant;
import java.util.LinkedList;
import java.util.List;

/**
 *
 * @author mike
 */
public class ReceivedMessage {
    protected final NATxM   message;
    protected final LinkedList<ReceivedFrame> frames;
    protected final long sequenceNumber;
    
    public ReceivedMessage(NATxM message,LinkedList<ReceivedFrame> frames,long sequenceNumber) {
        this.message = message;
        this.frames = new LinkedList<>(frames);
        this.sequenceNumber=sequenceNumber;
        if(frames.isEmpty()) {
            int y=10;
        }
    }

    public NATxM getMessage() {
        return message;
    }

    public Instant getReceiveTime() {
        if(frames.isEmpty()) {
            return null;
        }
        if(frames.size()==1) {
            return frames.iterator().next().getReceiveTime();
        }
        return frames.getLast().getReceiveTime();
    }

    public List<ReceivedFrame> getFrames() {
        return frames;
    }
    public boolean inTIM() {
        return message.isTIM();
    }
    public String getName() {
        return message.getName();
    }
    public int getLength() {
        return frames.size();
    }

    public long getSequenceNumber() {
        return sequenceNumber;
    }
    
}
