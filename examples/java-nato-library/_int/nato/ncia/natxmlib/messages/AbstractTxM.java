/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib.messages;

import _int.nato.ncia.natxmlib.HICDataFrame;
import _int.nato.ncia.natxmlib.JTIDSDataFrame;
import _int.nato.ncia.natxmlib.types.Field;
import _int.nato.ncia.natxmlib.types.FieldType;
import _int.nato.ncia.natxmlib.types.GenericMessageField;
import _int.nato.ncia.natxmlib.types.NamedField;
import java.util.Iterator;
import java.util.Map;
import java.util.TreeMap;

/**
 *
 * @author mike
 */
public abstract class AbstractTxM implements NATxM {

    protected int blockId;
    protected boolean isTIM;
    protected Map<String, NamedField> map;

    public AbstractTxM(int blockId, boolean isTIM, Iterable<Field> fields) {
        this.blockId = blockId;
        this.isTIM = isTIM;
        this.map = new TreeMap<>();
        for (Field f : fields) {
            if (f instanceof NamedField) {
                map.put(((NamedField) f).getName(), (NamedField) f);
            }
        }
    }

    public void addField(Field f) {
        if (f instanceof NamedField) {
            map.put(((NamedField) f).getName(), (NamedField) f);
        }
    }
    public void addField(String name, int wordId, int wordOfs,FieldType type) {
        addField(new GenericMessageField<>(name, type, wordId * 32 + wordOfs, 0));
    }
    public void addField(String name, int wordId, int wordOfs,FieldType type, long code) {
        addField(new GenericMessageField<>(name, type, wordId * 32 + wordOfs, code));
    }
    @Override
    public boolean isTIM() {
        return isTIM;
    }

    @Override
    public int getBlockId() {
        return blockId;
    }

    public Field getField(String name) {
        return map.get(name);
    }

    public int getInteger(String name) {
        return ((Field<Integer>) (map.get(name))).getValue();
    }
    public boolean getBoolean(String name, boolean defValue) {
        Field<Boolean> f = (Field<Boolean>) (map.get(name));
        if (f == null) {
            return defValue;
        } else {
            return f.getValue();
        }
    }
    @Override
    public Iterable<Field> fields() {
        return new Iterable<Field>() {
            @Override
            public Iterator<Field> iterator() {
                return new Iterator<Field>() {
                    Iterator<NamedField> iter = map.values().iterator();

                    @Override
                    public boolean hasNext() {
                        return iter.hasNext();
                    }

                    @Override
                    public Field next() {
                        return (Field) iter.next();
                    }
                };
            }
        };
    }

    @Override
    public String getName() {
        return isTIM ? ("TIM0" + blockId) : ("TOM0" + blockId);
    }

    @Override
    public JTIDSDataFrame[] encode() {
        HICDataFrame frame = HICDataFrame.create();
        for (Field f : map.values()) {
            frame.setCode(f.getOffset() / 32, f.getOffset() % 32, f.getLength(), (int) f.getCode());
        }
        return new JTIDSDataFrame[]{frame};
    }

}
