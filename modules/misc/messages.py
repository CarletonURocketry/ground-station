def printCURocket(rocket_name, version, author):
    print(fr"""
           ^
          / \
         /___\
        |=   =|              |\___/|
        |     |             /       \
        | C U |             |    /\__/|
        | I N |             ||\  <.><.>
        |Space|             | _     > )
        |     |             \   /----
        |     |              |   -\/
       /|##!##|\             /     \
      / |##!##| \
     /  |##!##|  \
    |  / ^ | ^ \  |
    | /  ( | )  \ |
    |/   ( | )   \|
        ((   ))
       ((  :  ))            CU InSpace Avionics Ground Station
       ((  :  ))            {f"Rocket": <10}{rocket_name}
        ((   ))             {f"Version": <10}{version}
          ( )               {f"Author": <10}{author}
              """)
