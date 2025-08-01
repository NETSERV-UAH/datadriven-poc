/* -*- P4_16 -*- */
#include <core.p4>
#include <v1model.p4>

const bit<16> TYPE_IPV4 = 0x800;
const bit<16> TYPE_ARP = 0x806;
const bit<32> MAX_RECORDS = 1<<16;
const bit<9> DROP_PORT = 511;
// ARP-specific types
enum bit<16> arp_opcode_t {
    REQUEST = 1,
    REPLY   = 2
}
/*************************************************************************
*********************** H E A D E R S  ***********************************
*************************************************************************/

typedef bit<9>  egressSpec_t;
typedef bit<48> macAddr_t;
typedef bit<32> ip4Addr_t;

header ethernet_t {
    macAddr_t dstAddr;
    macAddr_t srcAddr;
    bit<16>   etherType;
}

header arp_h{
    bit<16>       hw_type;
    bit<16>	  proto_type;
    bit<8>        hw_addr_len;
    bit<8>        proto_addr_len;
    arp_opcode_t  opcode;
}

header arp_ipv4_h {
    macAddr_t   src_hw_addr;
    ip4Addr_t  src_proto_addr;
    macAddr_t   dst_hw_addr;
    ip4Addr_t  dst_proto_addr;
}

header ipv4_t {
    bit<4>    version;
    bit<4>    ihl;
    bit<8>    diffserv;
    bit<16>   totalLen;
    bit<16>   identification;
    bit<3>    flags;
    bit<13>   fragOffset;
    bit<8>    ttl;
    bit<8>    protocol;
    bit<16>   hdrChecksum;
    ip4Addr_t srcAddr;
    ip4Addr_t dstAddr;
}

struct metadata {
    bit<1> is_arp;
    egressSpec_t table_out_port;
    bit<1> ipv4_forwarded;
    /* empty */
}

struct headers {
    ethernet_t   ethernet;
    arp_h	 arp;
    arp_ipv4_h	 arp_ipv4;
    ipv4_t       ipv4;
}

/*************************************************************************
*********************** R E G I S T E R  ***********************************
*************************************************************************/
register <egressSpec_t> (MAX_RECORDS) ucast_register_port;

/*************************************************************************
*********************** P A R S E R  ***********************************
*************************************************************************/

parser MyParser(packet_in packet,
                out headers hdr,
                inout metadata meta,
                inout standard_metadata_t standard_metadata) {

    state start {
        packet.extract(hdr.ethernet);
        transition select(hdr.ethernet.etherType){
            TYPE_ARP: parse_arp;
            TYPE_IPV4: parse_ipv4;
            default: accept;
        }
    }

    state parse_arp {
        packet.extract(hdr.arp);
        transition select(hdr.arp.hw_type, hdr.arp.proto_type) {
            (0x0001, TYPE_IPV4) : parse_arp_ipv4;
            default: accept;
        }
    }

    state parse_arp_ipv4 {
        packet.extract(hdr.arp_ipv4);
        transition accept;
    }

    state parse_ipv4 {
        packet.extract(hdr.ipv4);
        transition accept;
    }

}


/*************************************************************************
************   C H E C K S U M    V E R I F I C A T I O N   *************
*************************************************************************/

control MyVerifyChecksum(inout headers hdr, inout metadata meta) {
    apply {  }
}


/*************************************************************************
**************  I N G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyIngress(inout headers hdr,
                  inout metadata meta,
                  inout standard_metadata_t standard_metadata) {

    counter(MAX_RECORDS, CounterType.packets) StationsTrafficCounter;

    action drop() {
        mark_to_drop(standard_metadata);
    }

    action ipv4_forward() {
        //set the output port from the metadata table
        standard_metadata.egress_spec = meta.table_out_port;

        //decrease ttl by 1
        hdr.ipv4.ttl = hdr.ipv4.ttl -1;

	    // Set ipv4_forwarded to 1 
	    // This is doneto indicate that the decision has been to forward. This is used for the counter since it cannot be increased here and if it is increased based in the out_port being distint from DROP_PORT, not known packets (those for which we dont have added any rule will increase counters)
	    meta.ipv4_forwarded = 1;
    }

    action flood(){
	    // Set mcast_grp as ingress_port to select the mcast group that does not floods through the ingress port (See mcast groups in controller)	
	    standard_metadata.mcast_grp = (bit<16>) standard_metadata.ingress_port;
    }

    table arp_lpm {
	    key = {
	        meta.is_arp: exact;
	    }
	    actions = {
	        flood;
	        drop;
	        NoAction;
	    }
	    size = 1024;
	    default_action = NoAction();
    }

    table ipv4_lpm {
        key = {
            hdr.ipv4.dstAddr: lpm;
	        hdr.ipv4.srcAddr: ternary;
	        standard_metadata.ingress_port: ternary;
        }
        actions = {
            ipv4_forward;
            drop;
            NoAction;
        }
        size = 1024;
        default_action = NoAction();
    }

    apply {
	    bit<32> hash_srcmac;
	    bit<32> hash_dstmac;
	    bit<32> hash_srcip4;
	    egressSpec_t table_port = 0;    
	    hash(hash_srcmac, HashAlgorithm.identity, (bit<48>) 0, { hdr.ethernet.srcAddr }, (bit<48>) MAX_RECORDS);
	    hash(hash_dstmac, HashAlgorithm.identity, (bit<48>) 0, { hdr.ethernet.dstAddr }, (bit<48>) MAX_RECORDS);
	    hash(hash_srcip4, HashAlgorithm.identity, (bit<32>) 0, { hdr.ipv4.srcAddr }, (bit<32>) MAX_RECORDS);

	    if (hdr.arp.isValid()){
            meta.is_arp = 1;

	        if (hdr.arp.opcode == arp_opcode_t.REQUEST){
	    	    // ARP REQUEST
	    	    ucast_register_port.write(hash_srcmac, standard_metadata.ingress_port);
	        	arp_lpm.apply();
	        }
	        else if (hdr.arp.opcode == arp_opcode_t.REPLY){
	    	    // ARP RESPONSE
	    	    ucast_register_port.read(table_port, hash_dstmac);
	    	    ucast_register_port.write(hash_srcmac, standard_metadata.ingress_port);
	    	    standard_metadata.egress_spec = table_port;
	        }
	    }
        //only if IPV4 the rule is applied. Therefore other packets will not be forwarded.
        if (hdr.ipv4.isValid()){
	        ucast_register_port.read(table_port, hash_srcmac);
	        if (table_port != standard_metadata.ingress_port){
	    	    ucast_register_port.write(hash_srcmac, standard_metadata.ingress_port);
	        }
	        ucast_register_port.read(meta.table_out_port, hash_dstmac);
            ipv4_lpm.apply();
    
	        if (meta.ipv4_forwarded == 1 && standard_metadata.ingress_port == 1){
	    	    StationsTrafficCounter.count(hash_srcip4);
	        }
        }
    }
}

/*************************************************************************
****************  E G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyEgress(inout headers hdr,
                 inout metadata meta,
                 inout standard_metadata_t standard_metadata) {
    apply {  }
}

/*************************************************************************
*************   C H E C K S U M    C O M P U T A T I O N   **************
*************************************************************************/

control MyComputeChecksum(inout headers hdr, inout metadata meta) {
     apply {
	update_checksum(
	    hdr.ipv4.isValid(),
            { hdr.ipv4.version,
	      hdr.ipv4.ihl,
              hdr.ipv4.diffserv,
              hdr.ipv4.totalLen,
              hdr.ipv4.identification,
              hdr.ipv4.flags,
              hdr.ipv4.fragOffset,
              hdr.ipv4.ttl,
              hdr.ipv4.protocol,
              hdr.ipv4.srcAddr,
              hdr.ipv4.dstAddr },
            hdr.ipv4.hdrChecksum,
            HashAlgorithm.csum16);
    }
}


/*************************************************************************
***********************  D E P A R S E R  *******************************
*************************************************************************/

control MyDeparser(packet_out packet, in headers hdr) {
    apply {

        //parsed headers have to be added again into the packet.
        packet.emit(hdr.ethernet);
	packet.emit(hdr.arp);
	packet.emit(hdr.arp_ipv4);
        packet.emit(hdr.ipv4);

    }
}

/*************************************************************************
***********************  S W I T C H  *******************************
*************************************************************************/

//switch architecture
V1Switch(
MyParser(),
MyVerifyChecksum(),
MyIngress(),
MyEgress(),
MyComputeChecksum(),
MyDeparser()
) main;
