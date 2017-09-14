from datetime import timedelta

from django.utils import timezone

from rest_framework import permissions, status
from rest_framework.decorators import (api_view,
                                       authentication_classes,
                                       permission_classes,
                                       throttle_classes,)
from rest_framework.response import Response
from rest_framework_expiring_authtoken.authentication import (ExpiringTokenAuthentication,)
from rest_framework.throttling import UserRateThrottle

from accounts.permissions import HasVerifiedEmail

from challenges.permissions import IsChallengeCreator
from challenges.utils import get_challenge_model, get_challenge_phase_model
from jobs.models import Submission
from jobs.serializers import (LastSubmissionDateTime,
                              LastSubmissionDateTimeSerializer,
                              SubmissionCount,
                              SubmissionCountSerializer,
                              )
from participants.models import Participant
from participants.serializers import (ParticipantCount,
                                      ParticipantCountSerializer,
                                      ParticipantTeamCount,
                                      ParticipantTeamCountSerializer,
                                      )
from .serializers import ChallengePhaseSubmissionAnalysisSerializer, LastSubmissionDateTimeAnalysisSerializer


@throttle_classes([UserRateThrottle])
@api_view(['GET', ])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail, IsChallengeCreator))
@authentication_classes((ExpiringTokenAuthentication,))
def get_participant_team_count(request, challenge_pk):
    """
        Returns the number of participant teams in a challenge
    """
    challenge = get_challenge_model(challenge_pk)
    participant_team_count = challenge.participant_teams.count()
    participant_team_count = ParticipantTeamCount(participant_team_count)
    serializer = ParticipantTeamCountSerializer(participant_team_count)
    return Response(serializer.data, status=status.HTTP_200_OK)


@throttle_classes([UserRateThrottle])
@api_view(['GET', ])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail, IsChallengeCreator))
@authentication_classes((ExpiringTokenAuthentication,))
def get_participant_count(request, challenge_pk):
    """
        Returns the number of participants in a challenge
    """
    challenge = get_challenge_model(challenge_pk)
    participant_teams = challenge.participant_teams.all()
    participant_count = Participant.objects.filter(team__in=participant_teams).count()
    participant_count = ParticipantCount(participant_count)
    serializer = ParticipantCountSerializer(participant_count)
    return Response(serializer.data, status=status.HTTP_200_OK)


@throttle_classes([UserRateThrottle])
@api_view(['GET', ])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail, IsChallengeCreator))
@authentication_classes((ExpiringTokenAuthentication,))
def get_submission_count(request, challenge_pk, duration):
    """
        Returns submission count for a challenge according to the duration
        Valid values for duration are all, daily, weekly and monthly.
    """
    # make sure that a valid url is requested.
    if duration.lower() not in ('all', 'daily', 'weekly', 'monthly'):
        response_data = {'error': 'Wrong URL pattern!'}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    challenge = get_challenge_model(challenge_pk)

    challenge_phase_ids = challenge.challengephase_set.all().values_list('id', flat=True)

    q_params = {'challenge_phase__id__in': challenge_phase_ids}
    since_date = None
    if duration.lower() == 'daily':
        since_date = timezone.now().date()

    elif duration.lower() == 'weekly':
        since_date = (timezone.now() - timedelta(days=7)).date()

    elif duration.lower() == 'monthly':
        since_date = (timezone.now() - timedelta(days=30)).date()
    # for `all` we dont need any condition in `q_params`
    if since_date:
        q_params['submitted_at__gte'] = since_date

    submission_count = Submission.objects.filter(**q_params).count()
    submission_count = SubmissionCount(submission_count)
    serializer = SubmissionCountSerializer(submission_count)
    return Response(serializer.data, status=status.HTTP_200_OK)


@throttle_classes([UserRateThrottle])
@api_view(['GET', ])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail, IsChallengeCreator))
@authentication_classes((ExpiringTokenAuthentication,))
def get_challenge_phase_submission_analysis(request, challenge_pk, challenge_phase_pk):
    """
    API to fetch
    1. The submissions count for challenge phase.
    2. The participated team count for challenge phase.
    """

    challenge = get_challenge_model(challenge_pk)

    challenge_phase = get_challenge_phase_model(challenge_phase_pk)

    submissions = Submission.objects.filter(challenge_phase__challenge=challenge,
                                            challenge_phase=challenge_phase)
    try:
        serializer = ChallengePhaseSubmissionAnalysisSerializer(submissions, many=True)
        if serializer.data:
            response_data = serializer.data[0]
            return Response(response_data, status=status.HTTP_200_OK)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@throttle_classes([UserRateThrottle])
@api_view(['GET', ])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail, IsChallengeCreator))
@authentication_classes((ExpiringTokenAuthentication,))
def get_last_submission_time(request, challenge_pk, challenge_phase_pk, submission_by):
    """
        Returns the last submission time for a particular challenge phase
    """
    challenge = get_challenge_model(challenge_pk)

    challenge_phase = get_challenge_phase_model(challenge_phase_pk)

    # To get the last submission time by a user in a challenge phase.
    if submission_by == 'user':
        last_submitted_at = Submission.objects.filter(created_by=request.user.pk,
                                                      challenge_phase=challenge_phase,
                                                      challenge_phase__challenge=challenge)
        last_submitted_at = last_submitted_at.order_by('-submitted_at')[0].created_at
        last_submitted_at = LastSubmissionDateTime(last_submitted_at)
        serializer = LastSubmissionDateTimeSerializer(last_submitted_at)
        return Response(serializer.data, status=status.HTTP_200_OK)

    else:
        response_data = {'error': 'Page not found!'}
        return Response(response_data, status=status.HTTP_404_NOT_FOUND)


@throttle_classes([UserRateThrottle])
@api_view(['GET', ])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail, IsChallengeCreator))
@authentication_classes((ExpiringTokenAuthentication,))
def get_last_submission_datetime_analysis(request, challenge_pk, challenge_phase_pk):
    """
    API to fetch
    1. To get the last submission time in a challenge phase.
    2. To get the last submission time in a challenge.
    """

    challenge = get_challenge_model(challenge_pk)

    challenge_phase = get_challenge_phase_model(challenge_phase_pk)

    submissions = Submission.objects.filter(challenge_phase__challenge=challenge,
                                            challenge_phase=challenge_phase)
    try:
        serializer = LastSubmissionDateTimeAnalysisSerializer(submissions, many=True)
        if serializer.data:
            response_data = serializer.data[0]
            return Response(response_data, status=status.HTTP_200_OK)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
