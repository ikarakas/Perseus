/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Interface.java to edit this template
 */
package _int.nato.ncia.natxmlib.messages;

import _int.nato.ncia.natxmlib.JTIDSDataFrame;
import _int.nato.ncia.natxmlib.types.Field;
import _int.nato.ncia.natxmlib.types.FieldType;
import _int.nato.ncia.natxmlib.types.GenericMessageField;

/**
 *
 * @author mike
 */
public interface NATxM {
    boolean isTIM();
    int getBlockId();
    Iterable<Field> fields();
    String getName();
    public static <K> GenericMessageField<K> buildField(JTIDSDataFrame frame, String name, int widx, int wofs, FieldType<K> type) {
        int code = frame.getCode(widx, wofs, type.getLength());
        return new GenericMessageField<>(name, type, widx * 32 + wofs, code);
    }
    public static <K> GenericMessageField<K> createField(String name, int widx, int wofs, FieldType<K> type, long code) {
        return new GenericMessageField<>(name, type, widx * 32 + wofs, code);
    }
    default JTIDSDataFrame[] encode() {
        throw new UnsupportedOperationException();
    }
}
