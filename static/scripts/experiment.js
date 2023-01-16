var my_node_id;

// Create the agent.
create_agent = function() {
  dallinger.createAgent()
    .done(function (resp) {
      my_node_id = resp.node.id;
      get_infos();
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
          resp = JSON.parse(resp)
          acceptance = resp.density[1] / (resp.density[1] + resp.density[0])
          // console.log(resp.likelyhood[0])
          if (Math.random() < acceptance) {  // option given to human
            if (sides_switched === false) {
              drawAnimal(animal_0, "left");
              drawAnimal(animal_1, "right");
            } else {
              drawAnimal(animal_1, "left");
              drawAnimal(animal_0, "right");
            }
            $(".submit-response").attr('disabled', false);
          }
          else {
            dallinger.post('/choice/' + my_node_id + '/' + 0 + '/' + 0)
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

submit_response = function(choice, human) {
  if (sides_switched === true) {
    choice = 1 - choice;
  }
  $(".submit-response").attr('disabled',true);
  // paper.clear();

  dallinger.post('/choice/' + my_node_id + '/' + choice + '/' + human)
    .then(function () {
      create_agent();
    });
};

//
// Draw the animal..
//
drawAnimal = function (animal, side) {
  // PPU = 50;

  if (side === "left") {
    $.ajax({
      url: 'https://mcmcp-vae.herokuapp.com',
      method: 'POST',
      // headers: {'Access-Control-Allow-Origin': 'https://haijiangyan.github.io/' },
      // contentType: 'application/json',
      data: `{"data": [[${animal.x}, ${animal.y}, ${animal.z}]]}`,
      // dataType: 'json',
      success: function (resp) {
        // console.log(resp)
        document.getElementById('img1').setAttribute( 'src', resp)
      },
      error: function () {
          console.log('error!')
      }
  });
  } else if (side === "right") {
    $.ajax({
      url: 'https://mcmcp-vae.herokuapp.com',
      method: 'POST',
      // headers: {'Access-Control-Allow-Origin': 'https://haijiangyan.github.io/' },
      // contentType: 'application/json',
      data: `{"data": [[${animal.x}, ${animal.y}, ${animal.z}]]}`,
      // dataType: 'json',
      success: function (resp) {
        // console.log(resp)
        document.getElementById('img2').setAttribute( 'src', resp)
      },
      error: function () {
          console.log('error!')
      }
  });
  }
};



