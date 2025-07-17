/*
 * Copyright (c) 2004 - 2012 NAMSA CSI Cell. All rights reserved.
 * 
 * The NAMSA CSI Cell is the copyright holder of all code below.
 * Do not copy, re-use or modify without permission.
 * 
 * NATO Unclassified.
 */
package _int.nato.ncia.ginslib.busmon;

import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetSocketAddress;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;

/**
 *
 * @author mkroe
 */
public class BusMonitorSocket {
    protected final int localPort;
    protected final DatagramSocket socket;

    public BusMonitorSocket(int localPort) throws java.io.IOException {
        this.localPort = localPort;
        this.socket = new DatagramSocket(null);
        this.socket.setReuseAddress(true);
        this.socket.bind(new InetSocketAddress(localPort));
    }

    public BusMonitorMessage receive() throws java.io.IOException {
        byte[] buffer = new byte[1024];
        DatagramPacket dp = new DatagramPacket(buffer, buffer.length);
        socket.receive(dp);
        if(dp.getLength()>0) {
            ByteBuffer bb= ByteBuffer.wrap(buffer,0,dp.getLength());
            return new BusMonitorMessage(bb.order(ByteOrder.LITTLE_ENDIAN));
        }
        return null;
    }
}
