from mongo_ops import *
import pprint

if __name__ == "__main__":
    #flow_stats, sess_stats, one_way_stats = query_db()

    '''
    for stat in flow_stats:
        pprint.pprint(stat)
    for sess in sess_stats:
        pprint.pprint(sess)
    
    for one_way in one_way_stats:
        pprint.pprint(one_way)
    
    flow_stats = query_all_flow_stats()
    for feat in flow_stats:
        pprint.pprint(feat)

    stat = query_flow_stats('flow_packet_inter_arrival_max')
    print('flow_packet_inter_arrival_max = ' + str(stat))

    sess = query_all_sess_stats('10.42.0.1', '10.42.0.52')
    pprint.pprint(sess)

    sess_stat = query_sess_stats('10.42.0.1', '10.42.0.52', 'highest_protocol')
    print('highest protocol = ' + str(sess_stat))
    '''
    #one_way = query_one_way_stats_src('10.42.0.52')
    #pprint.pprint(one_way)
    '''
    pprint.pprint(query_one_way_stats_src_dst('10.42.0.52', '10.42.0.1'))

    pprint.pprint(query_one_way_stats_src_dst_stat('10.42.0.52', '10.42.0.1', 'highest_protocol'))


    print(query_endpoints('10.42.0.52'))'''

    devices = query_devices()
    print(devices)
    for device in devices:
        pprint.pprint(device)
        #print(device_is_IoT(device))
