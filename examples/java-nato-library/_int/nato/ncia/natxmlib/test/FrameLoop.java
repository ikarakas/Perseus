/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib.test;

import _int.nato.ncia.natxmlib.JTIDSDataFrame;
import _int.nato.ncia.natxmlib.JTIDSDataFrameSink;
import _int.nato.ncia.natxmlib.JTIDSDataFrameSource;
import java.io.IOException;
import java.util.concurrent.LinkedBlockingQueue;

/**
 *
 * @author mike
 */
public class FrameLoop implements JTIDSDataFrameSource, JTIDSDataFrameSink{
    protected final LinkedBlockingQueue<JTIDSDataFrame> queue = new LinkedBlockingQueue<>(20); 
    protected boolean closed=false;
    
    @Override
    public JTIDSDataFrame read() throws IOException {
        try {
            return queue.take();
        } catch (InterruptedException ex) {
            throw new IOException(ex);
        }
    }

    @Override
    public void close() {
        closed=true;
    }

    @Override
    public void write(JTIDSDataFrame frame) throws IOException {
        try {
            queue.put(frame);
        } catch (InterruptedException ex) {
            throw new IOException(ex);
        }
    }    
}
