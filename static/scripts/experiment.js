var my_node_id;

// Create the agent.
create_agent = function() {
  dallinger.createAgent()
    .done(function (resp) {
      my_node_id = resp.node.id;

      if (resp.node.type === 'MCMCP_agent') {
      get_infos();  
      } else {
      document.getElementById('img1').setAttribute( 'src', "static/images/236.jpg");
      document.getElementById('img2').setAttribute( 'src', "static/images/241.jpg");
      sides_switched = 0;
      start = new Date().getTime();
      $(".submit-response").attr('disabled', false);
      }
    })
    .fail(function (rejection) {
      // A 403 is our signal that it's time to go to the questionnaire
      if (rejection.status === 403) {
        dallinger.allowExit();
        dallinger.goToPage('questionnaire');
      } else {
        dallinger.error(rejection);
      }
    });
};

get_infos = function() {
  dallinger.getInfos(my_node_id)
    .done(function (resp) {
      sides_switched = Math.random() < 0.5;  //randomly switch the side

      animal_0 = JSON.parse(resp.infos[0].contents);
      animal_1 = JSON.parse(resp.infos[1].contents);

      $.ajax({
        url: 'https://mcmcp-vae.herokuapp.com/fx/' + 1,  // 'index' here refers to face with a specific emotion
        method: 'POST',
        data: `{"data": [[${animal_0.x}, ${animal_0.y}, ${animal_0.z}], [${animal_1.x}, ${animal_1.y}, ${animal_1.z}]]}`,
        success: function (resp) {
          acceptance = resp.density[1] ** 0.8 / (resp.density[1] ** 0.8 + resp.density[0] ** 0.8)
          
          // console.log(resp.likelyhood[0])
          if (Math.random() < acceptance) {  // option given to human
            if (sides_switched === false) {
              drawAnimal(animal_0, animal_1);
            } else {
              drawAnimal(animal_1, animal_0);
            }

            start = new Date().getTime();

            $(".submit-response").attr('disabled', false);
          }
          else {
            dallinger.post('/choice/' + my_node_id + '/' + 0 + '/' + 0 + '/' + 0)
              .then(function () {
                create_agent();
              });
          }
        },
        error: function () {
            console.log('error!');
            create_agent();
        }
    });
    });
};

submit_response = function(choice) {
  end = new Date().getTime();
  if (sides_switched === true) {
    choice = 1 - choice;
  }
  $(".submit-response").attr('disabled',true);
  // paper.clear();
  response_time = end - start;

  dallinger.post('/choice/' + my_node_id + '/' + choice + '/' + 1 + '/' + response_time)
    .done(function(resp) {
      create_agent();
    })
    .fail(function (rejection) {
      // A 403 is our signal that it's time to go to the questionnaire
      if (rejection.status === 403) {
        window.alert("Sorry, you are not focusing on the study, so you cannot move on this time. Please click 'OK' below to leave this page");
        dallinger.allowExit();
        dallinger.goToPage('questionnaire');}
       else {
        dallinger.error(rejection);
      }
     })
};

//
// Draw the animal..
//
drawAnimal = function (animal_left, animal_right) {

  $.ajax({
    url: 'https://mcmcp-vae.herokuapp.com',
    method: 'POST',
      // headers: {'Access-Control-Allow-Origin': 'https://haijiangyan.github.io/' },
      // contentType: 'application/json',
    data: `{"data": [[${animal_left.x}, ${animal_left.y}, ${animal_left.z}], [${animal_right.x}, ${animal_right.y}, ${animal_right.z}]]}`,
      // dataType: 'json',
    success: function (resp) {
        // console.log(resp)
      document.getElementById('img1').setAttribute( 'src', resp.left);
      document.getElementById('img2').setAttribute( 'src', resp.right);
    },
    error: function () {
        console.log('error!')
    }
  });
};



