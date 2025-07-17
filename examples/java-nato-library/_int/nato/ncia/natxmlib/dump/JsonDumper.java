/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib.dump;

import _int.nato.ncia.ginslib.GINSDecoder;
import _int.nato.ncia.ginslib.GINSMessage;
import _int.nato.ncia.ginslib.MessageType;
import _int.nato.ncia.ginslib.busmon.BusMonitorMessage;
import _int.nato.ncia.ginslib.busmon.CardMonFile;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.LinkedList;
import java.util.function.Consumer;
import java.util.logging.Level;
import java.util.logging.Logger;
import _int.nato.ncia.natxmlib.test.CommandLineArguments;

/**
 *
 * @author mike
 */
public class JsonDumper {
    protected final static ObjectMapper mapper = new ObjectMapper();
    protected static boolean toStdIO=false;
    
    static {
        mapper.registerModule(new JavaTimeModule());
        mapper.configure( SerializationFeature.WRITE_DATE_TIMESTAMPS_AS_NANOSECONDS, true );   
        mapper.enable(SerializationFeature.INDENT_OUTPUT);
    }   
  
    protected static void dumpBRF(Path inputFile, Path outputFile) throws IOException {
        LinkedList<BrfRecord> recordList = new LinkedList<>();
        try {
            CardMonFile.read(inputFile, new Consumer<BusMonitorMessage>() {
                @Override
                public void accept(BusMonitorMessage bm) {
                    MessageType mt = MessageType.identify(bm.getRT(), bm.isTransmit(), bm.getSA(), bm.getLength());
                    GINSMessage gm = GINSDecoder.decode(mt, bm);
                    recordList.add(new BrfRecord(bm, gm));
                }
            });
        } catch (IOException ex) {
            Logger.getLogger(JsonDumper.class.getName()).log(Level.SEVERE, null, ex);
        }
        if(toStdIO) {
            mapper.writeValue(System.out, recordList);
        }else{
            mapper.writeValue(outputFile.toFile(), recordList);
        }
    }
    public static void dump(Path inputFile) {
        if(!Files.exists(inputFile)) {
            System.err.append("File not found: "+inputFile.toString());
            return;
        }
        String inName = inputFile.getFileName().toString();
        String inExt=inName.substring(inName.lastIndexOf('.')+1,inName.length());
        
        switch(inExt.toLowerCase()) {
            case "brf":
                String outName=inName.substring(0,inName.length()-4)+".json";
                Path outputFile = inputFile.getParent().resolve(outName);
                try {
                    dumpBRF(inputFile, outputFile);
                }catch(IOException iex) {
                    System.err.append("Write exception: "+inputFile.toString()+";"+iex);                    
                }
                break;
            case "dat":
                break;
            case "raw":
                break;
            default: {
                System.err.append("Unknown file format: "+inputFile.toString());
                return;
            }
        }
    }
    public static void main(String[] args) {
        CommandLineArguments cla = new CommandLineArguments();
        cla.parse(args);
        if(cla.contains("stdio")) {
            toStdIO=true;
        }
        for(String fname : cla.getOptions("file")) {
            dump(Path.of(fname));                    
        }
    }
    public static class BrfRecord {
        protected BusMonitorMessage busMessage;
        protected GINSMessage ginsMessage;

        public BrfRecord(BusMonitorMessage busMessage, GINSMessage ginsMessage) {
            this.busMessage = busMessage;
            this.ginsMessage = ginsMessage;
        }

        public BusMonitorMessage getBusMessage() {
            return busMessage;
        }

        public GINSMessage getGINSMessage() {
            return ginsMessage;
        }
        
    }
}
