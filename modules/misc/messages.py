def printCURocket(call_sign, version, status):
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
       ((  :  ))            Call sign  {call_sign}
        ((   ))             Version    {version}
          ( )               Status     {status}
              """)
