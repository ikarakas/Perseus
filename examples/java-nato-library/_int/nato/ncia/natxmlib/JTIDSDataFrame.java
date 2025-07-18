/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Interface.java to edit this template
 */
package _int.nato.ncia.natxmlib;

/**
 *
 * @author mike
 */
public interface JTIDSDataFrame {
    int getWord(int idx);
    default int getCode(int widx, int bidx, int blen) {
        int word=getWord(widx);
        int value=0;
        for(int i=bidx;i<bidx+blen;i++) {
            int rmask=1<<i;
            int wmask=1<<(i-bidx);
            if((word & rmask)!=0) {
                value|=wmask;
            }
        }
        return value;
    }
    default void setCode(int widx, int bidx, int blen,int code) {
        int mask = ((int)((1L<<blen)-1))<<bidx;
        int scode = (code << bidx) & mask;
        int word = getWord(widx);
        int mword=(word & ~mask)|scode;
        setWord(widx, mword);
    }
    
    void setWord(int idx, int wvalue);
    byte[] getBytes();
}
