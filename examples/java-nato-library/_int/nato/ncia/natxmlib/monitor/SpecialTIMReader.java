/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib.monitor;

import _int.nato.ncia.natxmlib.DumpFile;
import _int.nato.ncia.natxmlib.JTIDSDataFrame;
import _int.nato.ncia.natxmlib.JTIDSDataFrameSource;
import _int.nato.ncia.natxmlib.NATIMReader;
import _int.nato.ncia.natxmlib.clock.SystemClock;
import _int.nato.ncia.natxmlib.messages.NATxM;
import java.io.IOException;
import java.time.Instant;
import java.util.LinkedList;
import java.util.function.Consumer;

/**
 *
 * @author mike
 */
public class SpecialTIMReader extends NATIMReader {
    protected final Consumer<ReceivedMessage> cons;
    
    protected long nextFrameSequenceNumber=1;
    protected long nextMessageSequenceNumber=1;
        
    public SpecialTIMReader(JTIDSDataFrameSource source, Consumer<ReceivedMessage> cons) {
        super(source);
        this.cons=cons;
    }

    @Override
    public NATxM read() throws IOException {
        NATxM txm = super.read();
        ReceivedMessage rm = new ReceivedMessage(txm, lastFrames,nextMessageSequenceNumber++);
        cons.accept(rm);
        lastFrames.clear();
        return txm;
    }
    protected final LinkedList<ReceivedFrame> lastFrames=new LinkedList<>();
    
    @Override
    protected JTIDSDataFrame readNextFrame() throws IOException {
        JTIDSDataFrame frame = super.readNextFrame();
        if(frame==null) {
            cons.accept(null);
        }
        Instant frameTime;
        long seqNumber;
        
        if(frame instanceof DumpFile.Record) {
            frameTime=((DumpFile.Record) frame).getTime();
            seqNumber=((DumpFile.Record) frame).getLineNumber();
        }else{
            frameTime=SystemClock.getInstance().now();
            seqNumber=nextFrameSequenceNumber++;
        }
        ReceivedFrame rframe = new ReceivedFrame(true, frame, frameTime,seqNumber);
        lastFrames.add(rframe);
        return frame;
    }
    
}
