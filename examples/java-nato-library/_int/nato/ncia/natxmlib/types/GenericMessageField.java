/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib.types;

/**
 *
 * @author mike
 */
public class GenericMessageField<K> implements NamedField<K> {
    protected final String name;
    protected final FieldType<K> type;
    protected final int offset;
    protected long code;
    protected K value;

    public GenericMessageField(String name, FieldType<K> type, int offset, long code) {
        this.name = name;
        this.type = type;
        this.offset = offset;
        this.code = code;
        this.value = type.decode(code);
    }
    
    @Override
    public FieldType<K> getType() {
        return type;
    }

    @Override
    public K getValue() {
        return value;
    }

    @Override
    public long getCode() {
        return code;
    }

    @Override
    public String getName() {
        return name;
    }

    @Override
    public int getOffset() {
        return offset;
    }
    
    @Override
    public String toString() {
        return "Field{name=" + name + ", value=" + value + ", code=" + code + ", offset=" + offset +"}";
    }

    @Override
    public int getLength() {
        return type.getLength();
    }

    @Override
    public void setCode(long code) {
        this.code=code;
    }
    @Override
    public void setValue(K value) {
        this.value=value;
        this.code=type.encode(value);
    }
}
