/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib;

import _int.nato.ncia.natxmlib.messages.GenericNATxM;
import _int.nato.ncia.natxmlib.messages.NATxM;
import _int.nato.ncia.natxmlib.messages.tim4.NATIM4_RequestReplyRecord;
import _int.nato.ncia.natxmlib.types.Field;
import _int.nato.ncia.natxmlib.types.FieldType;
import _int.nato.ncia.natxmlib.types.FieldTypes;
import _int.nato.ncia.natxmlib.types.GenericMessageField;
import _int.nato.ncia.natxmlib.types.IntegerType;
import java.util.LinkedList;

/**
 *
 * @author mike
 */
public class NATxMCodec {

    public static NATxM decodeTIM(JTIDSDataFrame frame) {
        int codeWI = frame.getCode(0, 0, 0);
        int codeBID = frame.getCode(0, 1, 5);
        if (codeWI != 0) {
            return null;
        }
        try {
            switch (codeBID) {
                case 4:
                    return decodeTIM4(frame);
                default:
                    return null;
            }
        } catch (Throwable t) {
            System.err.println("failed to decode TIM");
            return null;
        }
    }

    public static NATxM decodeTOM(JTIDSDataFrame frame) {
        int codeWI = frame.getCode(0, 0, 0);
        int codeBID = frame.getCode(0, 1, 5);
        if (codeWI != 0) {
            return null;
        }
        switch (codeBID) {
            case 4:
                return decodeTIM4(frame);
            default:
                return null;
        }
    }

    public static <K> GenericMessageField<K> buildField(JTIDSDataFrame frame, String name, int offset, FieldType<K> type) {
        int code = frame.getCode(offset / 32, offset % 32, type.getLength());
        return new GenericMessageField<>(name, type, offset, code);
    }

    public static <K> GenericMessageField<K> buildField(JTIDSDataFrame frame, String name, int widx, int wofs, FieldType<K> type) {
        int code = frame.getCode(widx, wofs, type.getLength());
        return new GenericMessageField<>(name, type, widx * 32 + wofs, code);
    }

    protected static NATxM decodeTIM4(JTIDSDataFrame frame) {
        LinkedList<Field> fieldList = new LinkedList<>();

        fieldList.add(buildField(frame, "WRAP INDICATOR", 0, 0, FieldTypes.BOOLEAN));
        fieldList.add(buildField(frame, "BLOCK ID", 0, 1, new IntegerType(5)));
        fieldList.add(buildField(frame, "TSR", 0, 7, FieldTypes.BOOLEAN));
        fieldList.add(buildField(frame, "TIME", 0, 8, FieldTypes.TIMESTAMP));
        fieldList.add(buildField(frame, "REQUEST_REPLY_1", 1, 0, NATIM4_RequestReplyRecord.TYPE));
        fieldList.add(buildField(frame, "REQUEST_REPLY_2", 2, 0, NATIM4_RequestReplyRecord.TYPE));
        fieldList.add(buildField(frame, "REQUEST_REPLY_3", 3, 0, NATIM4_RequestReplyRecord.TYPE));
        Field<Boolean> pfv = buildField(frame, "POSITION FIX VALID", 4, 31, FieldTypes.BOOLEAN);
        fieldList.add(pfv);
        if (pfv.getValue()) {
            fieldList.add(buildField(frame, "ALTITUDE QUALITY", 4, 27, new IntegerType(4)));
            fieldList.add(buildField(frame, "ALTITUDE", 4, 0, new IntegerType(23)));
            fieldList.add(buildField(frame, "LONGITUDE", 5, 0, FieldTypes.LONGITUDE));
            fieldList.add(buildField(frame, "LATITUDE", 6, 0, FieldTypes.LATITUDE));
            fieldList.add(buildField(frame, "POSITION QUALITY", 7, 16, new IntegerType(4)));
        }
        return new GenericNATxM(true, 4, fieldList.toArray(new Field[0]));

    }

}
