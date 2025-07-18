/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib.messages.tim4;

import _int.nato.ncia.natxmlib.JTIDSDataFrame;
import static _int.nato.ncia.natxmlib.NATxMCodec.buildField;
import _int.nato.ncia.natxmlib.messages.AbstractTxM;
import _int.nato.ncia.natxmlib.messages.NATxM;
import _int.nato.ncia.natxmlib.messages.tom4.NATOM04;
import _int.nato.ncia.natxmlib.messages.tom4.NATOM04.SyncStatus;
import _int.nato.ncia.natxmlib.types.Field;
import _int.nato.ncia.natxmlib.types.FieldTypes;
import _int.nato.ncia.natxmlib.types.IntegerType;
import java.util.LinkedList;
import java.util.List;

/**
 *
 * @author mike
 */
public class NATIM04 extends AbstractTxM {
    public NATIM04(List<Field> fields) {
        super(4, true, fields);
    }
    public static NATIM04 create() {
        LinkedList<Field> fields=new LinkedList<>();
        
        fields.add(NATxM.createField("WRAP INDICATOR", 0, 0, FieldTypes.BOOLEAN,0));
        fields.add(NATxM.createField("BLOCK ID", 0, 1, new IntegerType(5),4));
        fields.add(NATxM.createField("TIME SYNC REQUIRED", 0, 7, FieldTypes.BOOLEAN,0));
        fields.add(NATxM.createField("TIME", 0, 8, FieldTypes.TIMESTAMP,0));
        fields.add(NATxM.createField("REQUEST_REPLY_1", 1, 0, NATIM4_RequestReplyRecord.TYPE,0));
        fields.add(NATxM.createField("REQUEST_REPLY_2", 2, 0, NATIM4_RequestReplyRecord.TYPE,0));
        fields.add(NATxM.createField("REQUEST_REPLY_3", 3, 0, NATIM4_RequestReplyRecord.TYPE,0));
        
        return new NATIM04(fields);
    }

    public static NATIM04 decode(JTIDSDataFrame frame) {
        List<Field> fieldList = new LinkedList<>();

        fieldList.add(buildField(frame, "WRAP INDICATOR", 0, 0, FieldTypes.BOOLEAN));
        fieldList.add(buildField(frame, "BLOCK ID", 0, 1, new IntegerType(5)));
        fieldList.add(buildField(frame, "TIME SYNC REQUIRED", 0, 7, FieldTypes.BOOLEAN));
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
        return new NATIM04(fieldList);
    }
}
