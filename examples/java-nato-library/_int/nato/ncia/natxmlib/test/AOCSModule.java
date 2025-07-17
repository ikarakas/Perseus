/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib.test;

import aocslib.DataElement;
import aocslib.MulticastClass;
import aocslib.decoder.DefaultDecoder;
import aocslib.net.MASESocket;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.time.Instant;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Collection;
import java.util.Collections;

/**
 *
 * @author mike
 */
public class AOCSModule {

    protected int session = 19;
    protected String multicastInterface = "147.21.1.100";
    protected final static AOCSModule INSTANCE = new AOCSModule();

    public static AOCSModule getInstance() {
        return INSTANCE;
    }
    protected MASESocket aocsSocket = null;

    public void init() throws IOException {
        aocsSocket = new MASESocket(session, MulticastClass.RAP, multicastInterface);
        aocsSocket.joinGroup();
    }

    public boolean transmit(DataElement de) {
        if (aocsSocket == null) {
            try {
                init();
            } catch (IOException ex) {
                return false;
            }
        }
        aocsSocket.send(de);
        return true;
    }

    public Iterable<DataElement> receive() throws IOException {
        if (aocsSocket == null) {
            init();
        }

        byte[] buffer = new byte[65536];
        int len = aocsSocket.receiveData(buffer);
        if (len < 0) {
            return null;
        }
        try {
            Collection<DataElement> delist = DefaultDecoder.decode(buffer, len);
            return delist;
        }catch(Exception ex) {
            return Collections.EMPTY_LIST;
        }

    }

    protected FileOutputStream aocsWriteFile = null;

    public boolean write(DataElement de) {
        try {
            if (aocsWriteFile == null) {
                DateTimeFormatter tdf = DateTimeFormatter.ofPattern("yyyyMMdd_HHmmss");
                Instant detime = Instant.ofEpochMilli(de.getHeader().getTimeSeconds() * 1000 + de.getHeader().getTimeMicroseconds() / 1000);
                ZonedDateTime zdt = ZonedDateTime.ofInstant(detime, ZoneId.of("UTC"));
                String dts = tdf.format(zdt);
                try {
                    aocsWriteFile = new FileOutputStream("data/aocs_" + dts + ".dat");
                } catch (FileNotFoundException ex) {
                    return false;
                }
            }
            Instant time = Instant.ofEpochMilli(de.getTime());
            aocsWriteFile.write(de.getHeader().getBytes());
            aocsWriteFile.write(de.getContentData());
            return true;
        } catch (IOException ex) {
            return false;
        }
    }

    public void close() {
        if (aocsWriteFile != null) {
            try {
                aocsWriteFile.close();
            } catch (IOException ex) {
            }
        }
        if (aocsSocket != null) {
            aocsSocket.close();
        }
    }
}
