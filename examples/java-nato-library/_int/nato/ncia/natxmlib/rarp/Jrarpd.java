package _int.nato.ncia.natxmlib.rarp;

/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 */


import java.io.IOException;
import java.net.Inet4Address;
import java.net.InetAddress;
import java.net.UnknownHostException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.List;
import java.util.logging.Level;
import java.util.logging.Logger;

import org.pcap4j.core.NotOpenException;
import org.pcap4j.core.PacketListener;
import org.pcap4j.core.PcapAddress;
import org.pcap4j.core.PcapHandle;
import org.pcap4j.core.PcapNativeException;
import org.pcap4j.core.PcapNetworkInterface;
import org.pcap4j.core.PcapNetworkInterface.PromiscuousMode;
import org.pcap4j.core.Pcaps;
import org.pcap4j.packet.Packet;
import org.pcap4j.util.LinkLayerAddress;
import org.pcap4j.util.NifSelector;

/**
 *
 * @author kroen
 */
public class Jrarpd {
    public static String strTargetIp = "192.168.122.2";
    protected static String strNetworkInterfaceIp = null;
    protected static byte[] ownIp;
    protected static byte[] ownMAC;

    public static PcapNetworkInterface lookupNif(String addrString) throws IOException {
        List<PcapNetworkInterface> allDevs = null;

        try {
            allDevs = Pcaps.findAllDevs();
        } catch (PcapNativeException e) {
            throw new IOException(e.getMessage());
        }

        if (allDevs == null || allDevs.isEmpty()) {
            throw new IOException("No NIF to capture.");
        }
        for (PcapNetworkInterface nif : allDevs) {
            for (PcapAddress addr : nif.getAddresses()) {
                InetAddress ia = addr.getAddress();
                if (ia != null) {
                    if (ia.toString().startsWith(addrString)) {
                        ownIp = ia.getAddress();
                        for (LinkLayerAddress lla : nif.getLinkLayerAddresses()) {
                            if (lla.length() == 6) {
                                ownMAC = lla.getAddress();
                                break;
                            }
                        }

                        return nif;
                    }
                }
            }
        }
        return null;
    }

    public static byte[] generateResponse(byte[] reqMAC, InetAddress targetIp) {
        ByteBuffer bb = ByteBuffer.allocate(60).order(ByteOrder.BIG_ENDIAN);
        bb.put(reqMAC);
        bb.put(ownMAC);
        bb.putShort((short)0x8035);
        bb.putShort((short)1);
        bb.putShort((short)0x0800);
        bb.put((byte)6);
        bb.put((byte)4);
        bb.putShort((short)4);
        bb.put(ownMAC);
        bb.put(ownIp);
        bb.put(reqMAC);
        bb.put(targetIp.getAddress());
        return bb.array();
    }

    public static void process(PcapNetworkInterface device, PcapHandle handle, byte[] data) {
        ByteBuffer bb = ByteBuffer.wrap(data).order(ByteOrder.BIG_ENDIAN);
        byte[] etherDstMAC = new byte[6];
        bb.get(etherDstMAC);
        byte[] etherSrcMAC = new byte[6];
        bb.get(etherSrcMAC);
        int type = Short.toUnsignedInt(bb.getShort());
        if (type != 0x8035) {
            return;
        }
        int hwAddrType = Short.toUnsignedInt(bb.getShort());
        if (hwAddrType != 1) {
            return;
        }
        int protoAddrType = Short.toUnsignedInt(bb.getShort());
        if (protoAddrType != 0x0800) {
            return;
        }
        int hwLen = Byte.toUnsignedInt(bb.get());
        if (hwLen != 6) {
            return;
        }
        int protoLen = Byte.toUnsignedInt(bb.get());
        if (protoLen != 4) {
            return;
        }
        int opCode = Short.toUnsignedInt(bb.getShort()); //3=REQ, 4=REPLY
        if (opCode != 3) {
            return;
        }
        byte[] srcMAC = new byte[6];
        bb.get(srcMAC);
        byte[] srcIp = new byte[4];
        bb.get(srcIp);
        byte[] dstMAC = new byte[6];
        bb.get(dstMAC);
        byte[] dstIp = new byte[4];
        bb.get(dstIp);
        InetAddress ia4;
        try {
            ia4 = Inet4Address.getByName(strTargetIp);
        } catch (UnknownHostException ex) {
            return;
        }
        byte[] respData = generateResponse( srcMAC, ia4);
        if((respData!=null) && (handle!=null)) {
            try {
                handle.sendPacket(respData);
                System.out.println("RARPD: response sent");
                
            } catch (NotOpenException ex) {
                Logger.getLogger(Jrarpd.class.getName()).log(Level.SEVERE, null, ex);
            } catch (PcapNativeException ex) {
                Logger.getLogger(Jrarpd.class.getName()).log(Level.SEVERE, null, ex);
            }
        }
    }
    public static void capture(PcapNetworkInterface device) throws PcapNativeException, NotOpenException {
        if (device == null) {
            return;
        }
        int snapshotLength = 65536; // in bytes   
        int readTimeout = 50; // in milliseconds                   
        final PcapHandle handle;
        handle = device.openLive(snapshotLength, PromiscuousMode.PROMISCUOUS, readTimeout);

        PacketListener listener = new PacketListener() {
            @Override
            public void gotPacket(Packet packet) {
                process(device, handle, packet.getRawData());
            }
        };
        System.out.println("RARPD: listening");
        try {
            handle.loop(-1, listener);
        } catch (InterruptedException e) {
        }

        // Cleanup when complete
        handle.close();
    }
    public static void main_windows(String[] args) {
        String prop = System.getProperty("jna.library.path");
        if (prop == null || prop.isEmpty()) {
            prop = "C:/Windows/System32/Npcap";
        } else {
            if(!prop.contains("C:/Windows/System32/Npcap")) {
                prop += ";C:/Windows/System32/Npcap";
            }
        }
        System.setProperty("jna.library.path", prop);

        // The class that will store the network device
        // we want to use for capturing.
        PcapNetworkInterface device = null;

        // Pcap4j comes with a convenient method for listing
        // and choosing a network interface from the terminal
        try {
            // List the network devices available with a prompt
            device=lookupNif("/"+strNetworkInterfaceIp);
            if(device==null) {
                System.err.println("RARPD: interface matching "+strNetworkInterfaceIp+" not found");                            
            }else{
                capture(device);
            }
        } catch (Exception e) {
            System.err.println("RARPD: failed");            
        }        
    }

    public static void main(String[] args) {
        if(strNetworkInterfaceIp==null) {
            strNetworkInterfaceIp=strTargetIp.substring(0,strTargetIp.lastIndexOf(".")+1);
        }
        if(System.getProperty("os.name").toLowerCase().contains("win")) {
            main_windows(args);
        }else{            
        }
    }
    public static Runnable SERVER=new Runnable() {
        @Override
        public void run() {
            main(new String[0]);
        }
    };
}
