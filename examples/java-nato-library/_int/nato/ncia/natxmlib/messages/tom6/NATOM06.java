/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib.messages.tom6;

import _int.nato.ncia.natxmlib.JTIDSDataFrame;
import _int.nato.ncia.natxmlib.messages.AbstractTxM;
import static _int.nato.ncia.natxmlib.messages.NATxM.buildField;
import _int.nato.ncia.natxmlib.types.Field;
import _int.nato.ncia.natxmlib.types.FieldTypes;
import _int.nato.ncia.natxmlib.types.IntegerType;
import java.util.LinkedList;
import java.util.List;

/**
 *
 * @author mike
 */
public class NATOM06 extends AbstractTxM {

    public NATOM06(List<Field> fields) {
       super(6, false, fields);
    }
    public static NATOM06 decode(JTIDSDataFrame frame) {
        LinkedList<Field> fields = new LinkedList<>();
        fields.add(buildField(frame, "WRAP INDICATOR", 0, 0, FieldTypes.BOOLEAN));
        fields.add(buildField(frame, "BLOCK ID", 0, 1, new IntegerType(5)));
        fields.add(buildField(frame, "ET", 8, 0, FieldTypes.BOOLEAN));
        return new NATOM06(fields);
    }
 
}
