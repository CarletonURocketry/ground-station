def printCURocket(callsign, version, status):
    print(fr"""
           ^
          / \
         /___\
        |=   =|
        |     |
        | C U |
        | I N |
        |Space|
        |     |
        |     |
        |     |
       /|##!##|\
      / |##!##| \
     /  |##!##|  \
    |  / ^ | ^ \  |
    | /  ( | )  \ |
    |/   ( | )   \|
        ((   ))
       ((  :  ))            CU InSpace Telemetry Driver
       ((  :  ))            Callsign  {callsign}
        ((   ))             Version   {version}
          ( )               Status    {status}
              """)