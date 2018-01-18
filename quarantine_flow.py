##############################################################################
# This file contains code for blocking all traffic to/from a device          #
#                                                                            #
# File Name: qurantine_flow.py                                               #
# Author: Shashank Karthik Murali and Adithya Beemanapalli                   #
##############################################################################

def Q_flow(mac, i):
        return  [{
                      "priority": 20,
                      "timeout": 0,
                      "isPermanent": 'true',
                      "deviceId": "of:0000687f7429badf",
                      "treatment": {
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
                    }
                ][i]
