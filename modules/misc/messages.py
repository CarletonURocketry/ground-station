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
       /|##!##|\
      / |##!##| \
     /  |##!##|  \
    |  / ^ | ^ \  |
    | /  ( | )  \ |
    |/   ( | )   \|
        ((   ))
       ((  :  ))            CU InSpace Avionics Ground Station
       ((  :  ))            Call sign  {call_sign}
        ((   ))             Version    {version}
          ( )               Status     {status}
              """)
