from google.pubsub_v1.types.pubsub import PubsubMessage


def test_publish(publisher, mocker):
    topic_id = "test-topic-id"
    topic_path = f"projects/test-project-id/topics/{topic_id}"

    future = mocker.sentinel.future
    future.add_done_callback = mocker.Mock(spec=["__call__"])

    # Use a mock in lieu of the actual batch class.
    # pylint: disable=protected-access
    batch = mocker.Mock(spec=publisher._client._batch_class)

    # Set the mock up to accepts the message.
    batch.publish.side_effect = (future,)

    # pylint: disable=protected-access
    publisher._client._set_batch(topic_path, batch)

    # Publish message.
    future = publisher._publish(topic_id, b"test-message")
    assert future is mocker.sentinel.future

    # Check mock.
    batch.publish.assert_has_calls([mocker.call(PubsubMessage(data=b"test-message"))])
