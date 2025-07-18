package _int.nato.ncia.natxmlib;

import _int.nato.ncia.natxmlib.clock.SystemClock;
import _int.nato.ncia.natxmlib.messages.NATIM_Unknown;
import _int.nato.ncia.natxmlib.messages.NATIM;
import _int.nato.ncia.natxmlib.messages.NATIM_WRAP_AROUND;
import _int.nato.ncia.natxmlib.messages.NATxM;
import _int.nato.ncia.natxmlib.messages.tim1.NABIM01;
import _int.nato.ncia.natxmlib.messages.tim1.NATIM01;
import _int.nato.ncia.natxmlib.messages.tim3.NABIM03;
import _int.nato.ncia.natxmlib.messages.tim3.NATIM03;
import _int.nato.ncia.natxmlib.messages.tim4.NATIM04;
import java.io.IOException;
import java.util.LinkedList;

/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
/**
 *
 * @author mike
 */
public class NATIMReader {

    protected final JTIDSDataFrameSource source;
         
    public NATIMReader(JTIDSDataFrameSource source) {
        this.source = source;
    }
    protected JTIDSDataFrame readNextFrame() throws IOException {
        return source.read();
    }
    public NATIM decodeTIM01(JTIDSDataFrame frame0) throws IOException {
        NABIM01 bim0 = NABIM01.decode(frame0);
        if (bim0.getSubBlockId() != 1) {
            throw new IllegalArgumentException();
        }
        if (!bim0.isBFI()) {
            return NATIM01.decode(bim0);
        } else {
            JTIDSDataFrame frame1 = readNextFrame();
            NABIM01 bim1 = NABIM01.decode(frame1);
            if (bim1.getSubBlockId() != 2) {
                throw new IllegalArgumentException();
            }
            return NATIM01.decode(bim0, bim1);
        }
    }

    public NATIM03 decodeTIM03(JTIDSDataFrame frame0) throws IOException {
        NABIM03 bim0 = NABIM03.decode(frame0);
        if (bim0.getSubBlockId() != 1) {            
            throw new IllegalArgumentException("Expected TIM03 with subBlockId of 1, received subBlockId of "+bim0.getSubBlockId()+" instead!");
        }
        LinkedList<NABIM03> bimList = new LinkedList<>();
        bimList.add(bim0);
        for (int i = 2; (i < 7) && (i <= bim0.getSubBlockCount()); i++) {
            NABIM03 bimx = NABIM03.decode(readNextFrame());
            if (bimx.getSubBlockId() != i) {
                throw new IllegalArgumentException();
            }
            bimList.add(bimx);
        }
        return NATIM03.decode(bimList.toArray(new NABIM03[0]));
    }

    public NATxM read() throws IOException {
        JTIDSDataFrame frame = readNextFrame();
        
        if (frame == null) {
            return null;
        }
        try {
            int wi = frame.getCode(0, 0, 1);
            if (wi == 1) {
                return NATIM_WRAP_AROUND.decode(frame);
            }
            int blkId = frame.getCode(0, 1, 5);
 //           System.out.println(SystemClock.getInstance().now()+":received TIM "+blkId);
            switch (blkId) {
                case 1:
                    return decodeTIM01(frame);
                case 2:
                    return NATIM_Unknown.decode(frame);
                case 3:
                    return decodeTIM03(frame);
                case 4:
                    return NATIM04.decode(frame);
                case 5:
                    return NATIM_Unknown.decode(frame);
            }
        } catch (Throwable t) {
            System.out.println(t);
        }
        return NATIM_Unknown.decode(frame);

    }

    public void close() {
        source.close();
    }
}
