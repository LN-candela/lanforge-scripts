import importlib
import argparse
import sys
import logging
import os
import time
import csv
import pandas as pd
import re
import threading

logger = logging.getLogger(__name__)
if sys.version_info[0] != 3:
    logger.critical("This script requires Python 3")
    exit(1)


sys.path.append(os.path.join(os.path.abspath(__file__ + "../../../")))

lfcli_base = importlib.import_module("py-json.LANforge.lfcli_base")
LFCliBase = lfcli_base.LFCliBase
LFUtils = importlib.import_module("py-json.LANforge.LFUtils")
realm = importlib.import_module("py-json.realm")
Realm = realm.Realm
lf_logger_config = importlib.import_module("py-scripts.lf_logger_config")
lf_modify_radio = importlib.import_module("py-scripts.lf_modify_radio")
add_sta = importlib.import_module("py-json.LANforge.add_sta")
lanforge_api = importlib.import_module("lanforge_client.lanforge_api")
lf_report = importlib.import_module("py-scripts.lf_report")
lf_report = lf_report.lf_report
lf_graph = importlib.import_module("py-scripts.lf_graph")
lf_bar_graph = lf_graph.lf_bar_graph
lf_scatter_graph = lf_graph.lf_scatter_graph
lf_stacked_graph = lf_graph.lf_stacked_graph
lf_horizontal_stacked_graph = lf_graph.lf_horizontal_stacked_graph
lf_bar_graph_horizontal=lf_graph.lf_bar_graph_horizontal
from lf_base_interop_profile import RealDevice
from datetime import datetime, timedelta
interop_connectivity=importlib.import_module("py-json.interop_connectivity")

class Iperf(Realm):
    def __init__(self,mgr=None,radio=None,security=None,ssid=None,passwd=None,num_sta=None,
                 
                 start_id=None,
                 upstream_port=None,
                 duration=None,
                 bandwidth=None,
                 real_sta_list=None,
                 real_sta_data_dict=None,
                 virtual=None,
                 client_type=None,
                 streams=None,
                 traffic_type="",
                 direction="",
                 file_length=[],
                 filename=None,
                 band=None,
                 channel=None,
                 report_timer=1,
                 windows=None,
                 mac=None,

                 ):
         

         super().__init__(mgr) 
         self.mgr=mgr
         self.radio=radio
         self.security=security
         self.ssid =ssid
         self.passwd =passwd
         self.num_sta=num_sta
         self.upstream_port=upstream_port
         self.duration=duration
         self.bandwidth=bandwidth
         self.virtual=virtual
         self.client_type=client_type
         self.streams=streams
         self.traffic_type=traffic_type
         self.direction=direction
         self.csv_file_length=file_length
         self.filename=filename
         self.band=band
         self.channel=channel
         self.report_timer=report_timer
         self.windows=windows
         self.mac=mac
         print("report timer value",self.report_timer)

         

         
         
         self.start_id=start_id
         
         self.station_profile = self.new_station_profile()
         self.generic_endps_profile = self.new_generic_endp_profile()
         self.generic_endps_profile.dest=self.upstream_port
         self.generic_endps_profile.type="iperf3"
         self.Devices = None
         self.real_sta_list=real_sta_list
         self.real_sta_data_dict=real_sta_data_dict



         if self.traffic_type.lower()=='udp':
              self.traffic_type='-u'
         else:
              self.traffic_type=""

         if self.direction.lower() == "download":
            self.direction = "-R"
         elif self.direction.lower() == "upload":
            self.direction = ""

         
         if self.virtual:
              self.client_type="Virtual"
              
              self.station_list = LFUtils.port_name_series(prefix="sta",
                                            start_id=self.start_id,
                                            end_id=self.start_id + self.num_sta - 1,
                                            padding_number=10000,
                                            radio=self.radio)
         else:
              self.client_type="Real"
            
    #method to cleanup the resources     
    def cleanup(self):
         self.generic_endps_profile.cleanup()
         if(self.virtual):
              self.station_profile.cleanup(desired_stations=self.station_list)

    def check_tab_exists(self):
         print("check_tab_exists")

         response=self.json_get("generic")
         if response is None:
              return True
         else:
              return False
    
    
    def select_real_devices(self, real_devices, real_sta_list=None, base_interop_obj=None):
        #print("hello")
        if real_sta_list is None:
            #print("inside")
            self.real_sta_list, _, _ = real_devices.query_user()
        else:
            self.real_sta_list = real_sta_list
        if base_interop_obj is not None:
            #print("123")
            self.Devices = base_interop_obj

        # Need real stations to run interop test
        if (len(self.real_sta_list) == 0):
            logger.error('There are no real devices in this testbed. Aborting test')
            exit(0)

        logging.info(self.real_sta_list)
    def store_results_to_csv(self,result, csv_filename):
        #print(result)
        #print("store results to csv called")
        """ Writes results to a specified CSV file. """
        file_exists = os.path.isfile(csv_filename)
        for key,value in result.items():
             
            kbytes, kbits_sec = self.parse_values_from_string(value.get('last results', ''))
        
        #print("kybetsvalue ",kbytes)
        #print("kibts_secvalue ",kbits_sec)
        
        if kbytes and kbits_sec:
            with open(csv_filename, mode='a', newline='') as csv_file:

                #print("hello")
                csv_writer = csv.writer(csv_file)
                if not file_exists:
                    csv_writer.writerow(['Time', 'KBytes', 'Kbits/sec'])
                timestamp = time.time()
                formatted_timestamp = datetime.fromtimestamp(timestamp).strftime('%H:%M:%S')
                csv_writer.writerow([formatted_timestamp, kbytes, kbits_sec])

    def get_results(self):
        time.sleep(1)
        #print("get resulst called")
        logging.info(self.generic_endps_profile.created_endp)
        results = self.json_get(
            "/generic/{}".format(','.join(self.generic_endps_profile.created_endp)))
        if (len(self.generic_endps_profile.created_endp) > 1):
            results = results['endpoints']
        else:
            results = results['endpoint']
        
        return results
    def endpoint_0_handler(self,):
        #print("endpoint 0 handler called")
        results=self.get_results()
        result=results[0]
        """ Handles data processing for endpoint 0. """
        self.store_results_to_csv(result, 'endpoint_0_results.csv')
        result=results[1]
        """ Handles data processing for endpoint 1. """
        self.store_results_to_csv(result, 'endpoint_1_results.csv')

    # def endpoint_1_handler(self,):
    #     #
        
    #     #print("endpoint 1 handler called")
    #     results=self.get_results()
    #     result=results[1]
    #     """ Handles data processing for endpoint 1. """
    #     self.store_results_to_csv(result, 'endpoint_1_results.csv')

    def parse_values_from_string(self,s):
               # print(s)
                print("================================================")
                lines = s.split("\n")

                # if(len(lines)>=2):
                #      #print(lines[-2])
                # #print(parts)
                

                if(len(lines)>=2):
                    line=lines[-2]
                    #print("===============================================")
                    #print(line)
                    if 'KBytes' in line and 'Kbits/sec' in line:
                        parts=line.split()

                        kbytes_index = parts.index('KBytes') - 1
                        kbits_sec_index = parts.index('Kbits/sec') - 1

                        kbytes_value = parts[kbytes_index] if kbytes_index >= 0 else None
                        kbits_sec_value = parts[kbits_sec_index] if kbits_sec_index >= 0 else None

                        return kbytes_value, kbits_sec_value

                    else:
                            return None,None
                else:
                     return None,None
                    
        

        # Printing the extracted values
        #print("KBytes:", kbytes_value)
        #print("Kbits/sec:", kbits_sec_value)


        

        
        # Convert Mbits/sec to Kbits/sec by multiplying by 1000
        

    

    
        
        
    


    

    def change_upstream_to_ip(self):

            target_port_list = self.name_to_eid(self.upstream_port)
            shelf, resource, port, _ = target_port_list
            try:
                target_port_ip = self.json_get('/port/{}/{}/{}?fields=ip'.format(shelf, resource, port))['interface']['ip']
            except:
                logging.error('The target port {} not found on the LANforge. Please change the target.'.format(self.target))
                exit(0)
            self.upstream_port = target_port_ip
            self.generic_endps_profile.dest=self.upstream_port
            print(self.upstream_port)
    #method to create a station with ip address from dhcp
    def buildStation(self):
        self.station_profile.use_security(
            self.security, self.ssid, self.passwd)
        
        self.station_profile.set_command_param(
            "set_port", "report_timer", 1500)
        
        if self.station_profile.create(
            radio=self.radio,num_stations=self.num_sta,sta_names_=self.station_list):
            self._pass("Stations created.")
        else:
            self._fail("Stations not properly created.")


        self.station_profile.admin_up()
        if not LFUtils.wait_until_ports_admin_up(base_url=self.lfclient_url,
                                                     port_list=self.station_profile.station_names,
                                                     debug_=self.debug,
                                                     timeout=100):
                self._fail("Unable to bring all stations up")
                return
        if self.wait_for_ip(station_list=self.station_profile.station_names, timeout_sec=-1):
                self._pass("All stations got IPs", print_=True)
                self._pass("Station build finished", print_=True)
        else:
                self._fail("Stations failed to get IPs", print_=True)
                self._fail("FAIL: Station build failed", print_=True)
                logger.info("Please re-check the configuration applied")
    
    def get_final(self):
            results=self.get_results()
            print(results)
            print("=========================================================================")
            if(self.direction=="-R"):
                 result0=results[1]
                 result1=results[0]

            else:
                 
                 result0=results[0]
                 result1=results[1]

            datarate0=[]
            datarate1=[]
            
            for key,value in result0.items():
             
                  linestr=  value.get('last results', '')
                  lines=linestr.split('\n')
                  #print(lines)
                  print("====================================================================")
        
            
            for line in lines:
                # logging.info(line)
                values = line.split()
                #logging.info(values)
                #logging.info("length of the each line {}".format(len(values)))
                if len(values)==8:

                    
                    print(values[6])
                    datarate0.append(float(values[6]))
            
            if datarate0:  # Check if the list is not empty
                print("len of datarate0",len(datarate0))
                #datarate0.pop()
                average_datarate0 = sum(datarate0) / len(datarate0)
                average_datarate0=average_datarate0/1000
                print("Average Data Rate:", average_datarate0)
            else:
                print("No data to calculate the average.")

            
            
            for key,value in result1.items():
             
                  linestr=  value.get('last results', '')
                  lines=linestr.split('\n')
        
            
            for line in lines:
                # logging.info(line)
                values = line.split()
                logging.info(values)
                logging.info("length of the each line {}".format(len(values)))
                if len(values)==11:

                    
                    print(values[6])
                    datarate1.append(float(values[6]))
            if datarate1:  # Check if the list is not empty
                print("len of datareate1",len(datarate1))
                average_datarate1 = sum(datarate1) / len(datarate1)
                average_datarate1=average_datarate1/1000
                print("Average Data Rate:", average_datarate1)
            else:
                print("No data to calculate the average.")
            
                
                                   
                    

    
    def create_endpoint_client(self):
         self.generic_endps_profile.type = 'iperf3'
         #print(self.station_profile.station_names)
         #print(self.generic_endps_profile.created_endp)

         if(self.virtual):
              print(self.generic_endps_profile.created_endp)
              if self.generic_endps_profile.create(ports=self.station_profile.station_names,sleep_time=.5):
                #cmd = "iperf3 --forceflush --format k --precision 4 -c %s -t %s --tos 0 -b %sM --bind_dev %s -i 1 --pidfile /tmp/lf_helper_iperf3_%s.pid  -P %s %s %s" % (self.upstream_port,self.duration,self.bandwidth,self.station_list[0][4:],self.generic_endps_profile.created_endp[1],self.streams,self.traffic_type,self.direction)
                cmd="iperf3 --forceflush --format k --precision 4 -c %s -t %s %s %s --tos 0 -b %sM --bind_dev %s -i 1 --pidfile /tmp/lf_helper_iperf3_%s.pid" %(self.upstream_port,self.duration,self.traffic_type,self.direction,self.bandwidth,self.station_list[0][4:],self.generic_endps_profile.created_endp[1])
                self._pass("Generic endpoints creation completed.")
                print(self.generic_endps_profile.created_endp)
                self.generic_endps_profile.set_cmd(self.generic_endps_profile.created_endp[1], cmd)
              else:
                self._fail("Generic endpoints NOT completed.")
         else:
              if self.generic_endps_profile.create(ports=self.real_sta_list,sleep_time=.5):
                if self.windows:
                     cmd=".\iperf3.exe --forceflush --format k --precision 4 -c %s -t %s %s %s --tos 0 -b %sM -i 1 --pidfile lf_helper_iperf3_%s.pid -P %s" %(self.upstream_port,self.duration,self.traffic_type,self.direction,self.bandwidth,self.real_sta_list[0][6:],self.streams)
                     self.generic_endps_profile.set_cmd(self.generic_endps_profile.created_endp[1], cmd)
                elif self.mac:
                     cmd="iperf3 --forceflush --format k --precision 4 -c %s -t %s %s %s --tos 0 -b %sM -i 1 --pidfile lf_helper_iperf3_%s.pid" %(self.upstream_port,self.duration,self.traffic_type,self.direction,self.bandwidth,self.real_sta_list[0][6:])
                     self.generic_endps_profile.set_cmd(self.generic_endps_profile.created_endp[1], cmd)
                     
                else:
                     #cmd = "iperf3 --forceflush --format k --precision 4 -c %s -t %s --tos 0 -b %sM --bind_dev %s -i 1 --pidfile /tmp/lf_helper_iperf3_%s.pid  -P %s %s %s" % (self.upstream_port,self.duration,self.bandwidth,self.real_sta_list[0][6:],self.generic_endps_profile.created_endp[1],self.streams,self.traffic_type,self.direction)
                     cmd="iperf3 --forceflush --format k --precision 4 -c %s -t %s %s %s --tos 0 -b %sM --bind_dev %s -i 1 --pidfile /tmp/lf_helper_iperf3_%s.pid" %(self.upstream_port,self.duration,self.traffic_type,self.direction,self.bandwidth,self.real_sta_list[0][6:],self.generic_endps_profile.created_endp[1])
                     self.generic_endps_profile.set_cmd(self.generic_endps_profile.created_endp[1], cmd)
                
                     self._pass("Generic endpoints creation completed.")

              else:
                self._fail("Generic endpoints NOT completed.")
    def generate_report(self, result_json=None, result_dir='Iperf_test_Report', report_path=''):
        if result_json is not None:
            self.result_json = result_json
        logging.info('Generating Report')
        if self.traffic_type=='-u':
             self.traffic_type="UDP"
        else:
             self.traffic_type="TCP"

        if self.direction=="-R":
             self.direction="Download"
        else:
             self.direction="Upload"

        report = lf_report(_output_pdf='iperf-test.pdf',
                           _output_html='iperf-test.html',
                           _results_dir_name=result_dir,
                           _path=report_path)
        report_path = report.get_path()
        report_path_date_time = report.get_path_date_time()
        logging.info('path: {}'.format(report_path))
        logging.info('path_date_time: {}'.format(report_path_date_time))

        # setting report title
        report.set_title('Iperf Test Report')
        report.build_banner()

        # test setup info
        test_setup_info = {
            'SSID': self.ssid,
            'Security': self.security,
            'server': self.upstream_port,
            'Duration (in seconds)': self.duration,
            'IPerf Version':'Iperf3',
            'No of Clients':"1",
            'Client type':self.client_type,
            'No of parallel streams':self.streams,
            'Traffic Type':self.traffic_type+" "+self.direction,
            'Bandwidth':self.bandwidth+" Mbps",
            'Frequency Band':self.band+" GHz",
            'Channel':self.channel
            



        }
        print(test_setup_info)
        report.test_setup_table(
            test_setup_data=test_setup_info, value='Test Setup Information')

        # objective and description
        report.set_obj_html(_obj_title='Objective',
                            _obj='''The objective of the iperf test is to measure the througput
                            values of the network, it uses the tcp/udp (upload/download) traffic to send/recevie data from the client to server.
                            ''')
        report.build_objective()

        station = self.generic_endps_profile.created_endp[1]
        
        
        logging.info("inside the generate report {}".format(station))

        report.set_table_title('Iperf Test details')
        report.build_table_title()
        
        data = {
        'Iperf client': [station],
        'Iperf server': [self.generic_endps_profile.created_endp[0]],
        'Duration (in Seconds)': self.duration
        }

        dataframe2 = pd.DataFrame(data)
        report.set_table_dataframe(dataframe2)
        report.build_table()

        report.set_table_title('Iperf Test Results')
        report.build_table_title()
        #result=self.get_results()
        
    

        data = pd.read_csv('endpoint_0_results.csv')


        # Check if the 'Kbits/sec' column exists
        if 'Kbits/sec' in data.columns:
            # Calculate the average of the 'Kbits/sec' column
            endp0_avg = data['Kbits/sec'].mean()
            endp0_avg=endp0_avg/1000

            print(f"server average: {endp0_avg}")

        else:
            print("The column 'Kbits/sec' does not exist in the CSV file.")
        

        
        data = pd.read_csv('endpoint_1_results.csv')


        # Check if the 'Kbits/sec' column exists
        if 'Kbits/sec' in data.columns:
            # Calculate the average of the 'Kbits/sec' column
            endp1_avg = data['Kbits/sec'].mean()
            endp1_avg=endp1_avg/1000
            print(f"The average of client: {endp1_avg}")
        else:
            print("The column 'Kbits/sec' does not exist in the CSV file.")
        
        if self.direction=="Download":
                data = {
            'Wireless Client': [station],
            #'Data Recevied by client':tx_bytes,
            #'Data Sent by server':rx_bytes,
            'bps tx':endp0_avg,
            'bps rx':endp1_avg,
            }
        if self.direction=="Upload":
                data = {
            'Wireless Client': [station],
            #'Data sent by client':tx_bytes,
            #'Data received by server':rx_bytes,
            'bps tx':endp1_avg,
            'bps rx':endp0_avg,
            }
        

        dataframe1 = pd.DataFrame(data)
        report.set_table_dataframe(dataframe1)
        report.build_table()

        report.set_table_title(self.direction+' Throughput rate at every second')
        report.build_table_title()



        if(self.direction=="Download"):
             # Load the entire CSV file
            dataframe = pd.read_csv('endpoint_1_results.csv')
            dataframe['Kbits/sec'] = dataframe['Kbits/sec'].astype(int)

            dataframe['Kbits/sec'] = dataframe['Kbits/sec'] / 1000


            # Calculate which rows to read: start from the first data row (index 1), then every `report_timer + 1` row
            # Adding 1 to include the first data row in the intervals
            if self.report_timer==0:
                 self.report_timer=1
            rows_to_read = range(0, len(dataframe), self.report_timer+1)

            # Filter the DataFrame to only include the desired rows
            filtered_dataframe = dataframe.iloc[rows_to_read]

            # Now you can access the 'Kbits/sec' column or any processing
            dataset = filtered_dataframe['Kbits/sec']
            time = filtered_dataframe['Time'].tolist()
            print("len of the dataset",len(dataset))
            print('len of time',len(time))

            
        else:
              # Load the entire CSV file
            dataframe = pd.read_csv('endpoint_0_results.csv')
            dataframe['Kbits/sec'] = dataframe['Kbits/sec'].astype(int)

            dataframe['Kbits/sec'] = dataframe['Kbits/sec'] / 1000

            # Calculate which rows to read: start from the first data row (index 1), then every `report_timer + 1` row
            # Adding 1 to include the first data row in the intervals
            if self.report_timer==0:
                 self.report_timer=1
            rows_to_read = range(0, len(dataframe), self.report_timer)
            # Filter the DataFrame to only include the desired rows
            filtered_dataframe = dataframe.iloc[rows_to_read]

            # Now you can access the 'Kbits/sec' column or any processing
            #dataset = filtered_dataframe['Kbits/sec']

            #time = filtered_dataframe['Time'].tolist()
            #dataset = dataframe['Kbits/sec']
            #dataframe['Kbits/sec'] = dataframe['Kbits/sec'].astype(int)
            dataset = filtered_dataframe['Kbits/sec']

            time = filtered_dataframe['Time'].tolist()

            print("len of the dataset",len(dataset))
            print('len of time',len(time))


            
             

        base_height_per_category = 0.5  # half an inch per category
        minimum_height = 5              # minimum height of the graph in inches

        # Calculate the dynamic height
        dynamic_height = max(len(dataset) * base_height_per_category, minimum_height)
        
        
        graph = lf_bar_graph_horizontal(
                 _data_set=[dataset],
                 _xaxis_name="Throughput (in Mbps)",
                 _yaxis_name="Time (in sec)",
                 _yaxis_categories=time,
                 _yaxis_label=None,
                 _graph_title="Time (in sec) vs Throughput (in Mbps)",
                 _title_size=16,
                 _graph_image_name="image_name",
                 _label=[""],
                 _color=None,
                 _bar_height=0.70,
                 _color_edge='grey',
                 _font_weight='bold',
                 _color_name=None,
                 _figsize=(10,dynamic_height),
                 _show_bar_value=False,
                 _yaxis_step=1,
                 _yticks_font=None,
                 _yaxis_value_location=0,
                 _yticks_rotation=None,
                 _text_font=None,
                 _text_rotation=None,
                 _grp_title="",
                 _legend_handles=None,
                 _legend_loc="best",
                 _legend_box=None,
                 _legend_ncol=1,
                 _legend_fontsize=None,
                 _dpi=96,
                 _enable_csv=False,
                 _remove_border=None,
                 _alignment=None
        )



        graph_png = graph.build_bar_graph_horizontal()
        logging.info('graph name {}'.format(graph_png))
        report.set_graph_image(graph_png)
        # need to move the graph image to the results directoryreport
        report.move_graph_image()
        # report.set_csv_filename(graph_png)
        # report.move_csv_file()
        report.build_graph()


        # closing
        report.build_custom()
        report.build_footer()
        report.write_html()
        report.write_pdf()

                

    def create_endpoint_server(self):
         # creating a generic end point server
        self.generic_endps_profile.type = 'iperf3_serv'
        start_port=5201
        
             
        server_station = []
        server_station.append(self.upstream_port)
        logging.info('\n\n server station {}'.format(server_station))

        #for i in range(len(self.station_list)):
            #port =start_port+i
        if (self.generic_endps_profile.create(ports=server_station, sleep_time=.5)):
                        #print("Server endpoint on port {} created successfully".format(port))
                        print("server endpoint created successfully")
        

    
                
        else:
                logging.error('Virtual client generic endpoint creation failed.')
                exit(0)
    def start_generic(self):
         self.generic_endps_profile.start_cx()
    def stop_generic(self):
         self.generic_endps_profile.stop_cx()

    


def main():
    parser =argparse.ArgumentParser(description='LANforge Script with Command Line Arguments')
    
    #Command-line arguments for creating station
    parser.add_argument('--mgr',required=True,help='LANforge IP address')
    parser.add_argument('--radio', type=str, help='radio name')
    parser.add_argument('--security', type=str, help='security type')
    parser.add_argument('--ssid', type=str,help='ssid of accesspoint')
    parser.add_argument('--passwd', type=str, help='password')
    parser.add_argument('--num_sta', type=int, help='no of stations')
    parser.add_argument('--upstream_port',type=str,help='upstream port for running traffic')
    parser.add_argument('--duration',type=str,help="duration in which test should run")
    parser.add_argument('--bandwidth',type=str,help="bandwdith for test in Mbps")
    
    
    

    
    parser.add_argument('--start_id',type=int,help='mention the startid for the stations')

    parser.add_argument('--virtual',action='store_true',help='run the test with virtual clients')
    parser.add_argument('--filename',type=str,help='filename to store the results')
    parser.add_argument('--streams',type=str,help='no of parallel streams')
    parser.add_argument('--traffic_type',type=str,help='traffic type tcp/udp')
    parser.add_argument('--direction',type=str,help='direction of traffic whether it is download or upload')
    parser.add_argument('--band',type=str,help='frequency band')
    parser.add_argument('--channel',type=str,help='channel information')
    parser.add_argument('--report_timer',type=int,default=1,help="report timer")
    parser.add_argument('--windows',action='store_true',help='argument for windows')
    parser.add_argument('--mac',action='store_true',help='argument for windows')
    
    

    
     





    args = parser.parse_args()
    dur=args.duration[-1]
    print(dur)
    durtime=int(args.duration[0:len(args.duration)-1])
    print("duration time",durtime)
    if(dur=="m" or dur=="M"):
         durtime=durtime*60
    if(dur=="H" or dur=="h"):
         durtime=durtime*60*60
    


    iperfobj=Iperf(mgr=args.mgr,radio=args.radio,security=args.security,ssid=args.ssid,passwd=args.passwd,num_sta=args.num_sta,start_id=args.start_id,upstream_port=args.upstream_port,duration=durtime,bandwidth=args.bandwidth,virtual=args.virtual,streams=args.streams,traffic_type=args.traffic_type,direction=args.direction,filename=args.filename,band=args.band,channel=args.channel,report_timer=args.report_timer,windows=args.windows,mac=args.mac)
    if((iperfobj.check_tab_exists())):
         print("Please enable the generic tab")
         exit(0)
    

    iperfobj.cleanup()
    if args.virtual:
         iperfobj.buildStation()
    iperfobj.create_endpoint_server()
    if not args.virtual:
         devices = RealDevice(manager_ip=args.mgr,selected_bands='8g')
         devices.get_devices()
         iperfobj.select_real_devices(real_devices=devices)

    iperfobj.change_upstream_to_ip()
    iperfobj.create_endpoint_client()
    time.sleep(5)
    iperfobj.start_generic()
    

    for i in range(0,durtime):
         iperfobj.endpoint_0_handler()
         #iperfobj.endpoint_1_handler()
         #thread_0 = threading.Thread(target=iperfobj.endpoint_0_handler)
         #thread_1 = threading.Thread(target=iperfobj.endpoint_1_handler)

    # Start the threads
         #thread_0.start()
         #thread_1.start()

    # Wait for both threads to complete
         #thread_0.join()
         #thread_1.join()

         #time.sleep(1)
    #iperfobj.stop_generic()
    time.sleep(5)
    iperfobj.get_final()
    iperfobj.generate_report()
    
   

if __name__ =="__main__":
    main()


        