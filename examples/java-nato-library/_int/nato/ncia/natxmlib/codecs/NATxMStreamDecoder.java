/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib.codecs;

import _int.nato.ncia.natxmlib.JTIDSDataFrame;
import _int.nato.ncia.natxmlib.messages.GenericNATxM;
import _int.nato.ncia.natxmlib.messages.tom4.NATOM04;
import _int.nato.ncia.natxmlib.messages.tim4.NATIM04;
import _int.nato.ncia.natxmlib.messages.NATxM;
import _int.nato.ncia.natxmlib.messages.tim1.NABIM01;
import _int.nato.ncia.natxmlib.messages.tom1.NATOM01;
import _int.nato.ncia.natxmlib.messages.tom3.NABOM03;
import _int.nato.ncia.natxmlib.types.Field;
import java.util.Collections;
import java.util.LinkedList;
import java.util.List;
import java.util.function.Consumer;

/**
 *
 * @author mike
 */
public class NATxMStreamDecoder {

    protected final Consumer<NATxM> consumer;

    public NATxMStreamDecoder(Consumer<NATxM> consumer) {
        this.consumer = consumer;
    }

    protected final LinkedList<JTIDSDataFrame> tomFrameQueue = new LinkedList<>();

    public void onTOM(JTIDSDataFrame frame) {
        int wi = frame.getCode(0, 0, 1);
        int blkId = frame.getCode(0, 1, 5);
        try {
            switch (blkId) {
                case 1:
                    break;
                case 3:
                    consumer.accept(NABOM03.decode(frame));
                    break;                    
                case 4:
                    consumer.accept(NATOM04.decode(frame));
                    break;
                case 6:
                    consumer.accept(new GenericNATxM(false, blkId,new Field[0]));
                    break;
                default:
                    consumer.accept(new GenericNATxM(false, blkId,new Field[0]));
                    break;
            }
        } catch (Throwable t) {
            int y=10;
        }

    }
    protected final LinkedList<JTIDSDataFrame> timFrameQueue = new LinkedList<>();

    public void onTIM(JTIDSDataFrame frame) {
        int wi = frame.getCode(0, 0, 1);
        int blkId = frame.getCode(0, 1, 5);
        try {
            switch (blkId) {
                case 0:
                    consumer.accept(NABIM01.decode(frame));
                    break;
                case 1:
                    consumer.accept(NABIM01.decode(frame));
                    break;
                case 4:
                    consumer.accept(NATIM04.decode(frame));
                    break;
                default:
                    List l = Collections.EMPTY_LIST;
                    consumer.accept(new GenericNATxM(true, blkId,new Field[0]));
                    break;

            }
        } catch (Throwable t) {
            int y=10;
        }
    }

    public void finish() {

    }
}
