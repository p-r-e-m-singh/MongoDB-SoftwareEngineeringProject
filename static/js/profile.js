function load_content() {
    console.log("start")
    var name = document.getElementById("name").value;
    var job = document.getElementById("job").value;
    var city = document.getElementById("city").value;
    var phone = parseInt(document.getElementById("mobno").value);
    var server_data = [
        {"name": name},
        {"job": job},
        {"city": city},
        {"phone": phone}
      ];
          $.ajax({
              type: "POST",
              url: "/update_profile",
              data: JSON.stringify(server_data),
              contentType: "application/json",
              dataType: 'json' 
            });
            console.log('out')
      console.log("end")
  }
