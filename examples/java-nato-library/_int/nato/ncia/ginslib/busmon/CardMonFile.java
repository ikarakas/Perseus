/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.ginslib.busmon;

import java.io.IOException;
import java.io.InputStream;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.function.Consumer;

/**
 *
 * @author mike
 */
public class CardMonFile {
    public static void read(Path p, Consumer<BusMonitorMessage> cons) throws IOException {
        InputStream ins = Files.newInputStream(p, StandardOpenOption.READ);
        while(true) {
            byte[] rlen = ins.readNBytes(2);
            if(rlen==null) {
                break;
            }
            if(rlen.length!=2) {
                break;
            }
            int dataLength = Short.toUnsignedInt(ByteBuffer.wrap(rlen).order(ByteOrder.LITTLE_ENDIAN).getShort());
            byte[] data=ins.readNBytes(dataLength);
            if(data==null) {
                break;
            }
            BusMonitorMessage bm = new BusMonitorMessage(ByteBuffer.wrap(data));
            cons.accept(bm);
        }
    }
}
