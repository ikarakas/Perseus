/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib;

import _int.nato.ncia.natxmlib.dump.JsonDumper;
import _int.nato.ncia.natxmlib.test.CommandLineArguments;

/**
 *
 * @author mike
 */
public class Main {
    public static void main(String[] args) {
        CommandLineArguments cla = new CommandLineArguments();
        cla.parse(args);
        if(cla.contains("dump")) {
            JsonDumper.main(args);
        }
    }
}
