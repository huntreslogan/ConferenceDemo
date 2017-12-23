$(function () {
  console.log('Requesting Capability Token...');
  $.get('/capabilitytoken')
    .done(function (data) {
      console.log('Got a token.');
      console.log('Token: ' + data.token);

      // Setup Twilio.Device
      Twilio.Device.setup(data.token);

      Twilio.Device.ready(function (device) {
        console.log('Twilio.Device Ready!');

      });

      Twilio.Device.error(function (error) {
        console.log('Twilio.Device Error: ' + error.message);
      });

      Twilio.Device.connect(function (conn) {
        console.log('Successfully established call!');
      });

      Twilio.Device.disconnect(function (conn) {
        console.log('Call ended.');
      });
    })
    .fail(function (e) {
      console.error(e);
      console.log('Could not get a token from server!');
    });

    $('#leave-button').click(function() {
      Twilio.Device.disconnectAll();
      $('#leave-button').addClass('hide');
      $('#monitor-button').removeClass('hide');

    });

    $('#monitor-button').click(function () {

      console.log('Calling ...');
      Twilio.Device.connect();
      $('#monitor-button').addClass('hide');
      $('#leave-button').removeClass('hide');
    });

    $.getJSON('/token', function (tokenResponse) {
      //Initialize the Sync client
      console.log(tokenResponse.token);
      syncClient = new Twilio.Sync.Client(tokenResponse.token, { logLevel: 'info' });
      syncClient.on('connectionStateChanged', function(state) {
        if (state != 'connected') {
          console.log('Sync is not live (websocket connection ' + state);
        } else {
          console.log('Sync is live!');
        }
      });

      //Let's pop a message on the screen to show that Sync is ready
      console.log('Sync initialized!');


      //This code will create and/or open a Sync document
      //Note the use of promises
      // $('#leave-button').click(function() {
      //   Twilio.Device.disconnectAll();
      //   $('#monitor-button').removeClass('hide');
      // });
      //
      // $('#monitor-button').click(function () {
      //
      //   console.log('Calling ...');
      //   Twilio.Device.connect();
      //   $('#monitor-button').addClass('hide');
      //   $('#leave-button').removeClass('hide');
      // });

      syncClient.document("AgentData").then(function(doc) {
          doc.on("updated",function(data) {
          console.log(data);
          $('#monitor-button').attr('disabled', false);

        });
      });

      });

    });
