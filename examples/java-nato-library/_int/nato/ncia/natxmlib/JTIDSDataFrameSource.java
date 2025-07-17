/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Interface.java to edit this template
 */
package _int.nato.ncia.natxmlib;

import java.io.IOException;

/**
 *
 * @author mike
 */
public interface JTIDSDataFrameSource {
    JTIDSDataFrame read() throws IOException;
    void close();
}
