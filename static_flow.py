##############################################################################
# This file contains code for creating a flow based off of the trafic rules  #
# in the MUD file                                                            #
#                                                                            #
# File Name: static_flow.py                                                  #
# Author: Shashank Karthik Murali and Adithya Beemanapalli                   #
##############################################################################

def S_flow(mac, host1_ip, host2_ip, i):
        return  [{
                  "priority": 20,
                  "timeout": 0,
                  "tableId": 1,
                  "isPermanent": 'true',
                  "deviceId": "of:0000687f7429badf",
                  "treatment": {
                    "instructions": [
                      {
                        "type": "OUTPUT",
                        "port": "1"
                      }
                    ]
                  },
                  "selector": {
                    "criteria": [
                      {
                        "type": "IN_PORT",
                        "port": 2
                      },
                      {
                        "type": "ETH_SRC",
                        "mac": mac
                      },
                      {
                        "type": "ETH_DST",
                        "mac": "60:E3:27:9B:44:BF"
                      }
                    ]
                  }
                },

                {
                          "priority": 20,
                          "timeout": 0,
                          "isPermanent": 'true',
                          "deviceId": "of:0000687f7429badf",
                          "treatment": {
                            "instructions": [
                              {
                                "type": "OUTPUT",
                                "port": "2"
                              }
                            ]
                          },
                          "selector": {
                            "criteria": [
                              {
                                "type": "IN_PORT",
                                "port": 1
                              },
                              {
                                "type": "ETH_SRC",
                                "mac": "60:E3:27:9B:44:BF"
                              },
                              {
                                "type": "ETH_DST",
                                "mac": mac
                              }
                            ]
                          }
                    },

                    {
                          "priority": 20,
                          "timeout": 0,
                          "isPermanent": 'true',
                          "deviceId": "of:0000687f7429badf",
                          "treatment": {
                            "instructions": [
                              {
                                "type": "TABLE",
                                "tableId": 1
                              }
                            ]
                          },
                          "selector": {
                            "criteria": [
                              {
                                "type": "IN_PORT",
                                "port": 2
                              },
                              {
                                "type": "IPV4_SRC",
                                "ip": host1_ip
                              },
                              {
                                "type": "IPV4_DST",
                                "ip": host2_ip
                              },
                              {
                                "type": "ETH_TYPE",
                                "ethType": "0x0800"
                              }
                            ]
                          }
                        }
                        ][i]
