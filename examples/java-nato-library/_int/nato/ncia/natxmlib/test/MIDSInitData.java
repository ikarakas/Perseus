/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib.test;

import _int.nato.ncia.natxmlib.data.DataFieldDefinition;
import _int.nato.ncia.natxmlib.data.DataFieldView;
import _int.nato.ncia.natxmlib.data.WordDataStore;
import _int.nato.ncia.natxmlib.data.WordData;

/**
 *
 * @author mike
 */
public class MIDSInitData {

    protected final WordDataStore data = new WordDataStore();
    protected final DataFieldView fieldView = new DataFieldView(DataFieldDefinition.DataDomain.MIDS_INITIALIZATION, data);

    public MIDSInitData() {
    }

    public WordData getWordData() {
        return data;
    }
    public void setField(DataFieldDefinition dfd, int code) {
        fieldView.setCode(dfd, code);
    }
    public int wordCount(DataFieldDefinition dfd) {
        if (dfd.getOffset() + dfd.getLength() <= 16) {
            return 1;
        }else{
            return 1+((dfd.getOffset()+dfd.getLength())/16);
        }
    }
    
}
